/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import gov.anl.aps.logr.portal.model.db.beans.DomainFacade;
import gov.anl.aps.logr.portal.model.db.beans.ItemDomainLogbookFacade;
import gov.anl.aps.logr.portal.model.db.beans.ItemFacade;
import gov.anl.aps.logr.portal.model.db.beans.UserGroupFacade;
import gov.anl.aps.logr.portal.model.db.beans.UserInfoFacade;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import gov.anl.aps.logr.portal.utilities.ConfigurationUtility;
import gov.anl.aps.logr.rest.authentication.User;
import gov.anl.aps.logr.rest.authentication.UserSessionKeeper;
import gov.anl.aps.logr.rest.mcp.protocol.JsonRpcError;
import gov.anl.aps.logr.rest.mcp.protocol.JsonRpcRequest;
import gov.anl.aps.logr.rest.mcp.protocol.JsonRpcResponse;
import gov.anl.aps.logr.rest.mcp.protocol.McpProtocolException;
import gov.anl.aps.logr.rest.mcp.tools.McpArgumentException;
import gov.anl.aps.logr.rest.mcp.tools.McpTool;
import gov.anl.aps.logr.rest.mcp.tools.McpToolContext;
import gov.anl.aps.logr.rest.mcp.tools.McpToolRegistry;
import gov.anl.aps.logr.rest.mcp.tools.McpToolResult;
import gov.anl.aps.logr.rest.mcp.tools.impl.BelyGetLogDocumentTool;
import gov.anl.aps.logr.rest.mcp.tools.impl.BelyGetLogEntryTool;
import gov.anl.aps.logr.rest.mcp.tools.impl.BelyListLogDocumentsTool;
import gov.anl.aps.logr.rest.mcp.tools.impl.BelyListLogEntriesTool;
import gov.anl.aps.logr.rest.mcp.tools.impl.BelyListLookupsTool;
import gov.anl.aps.logr.rest.mcp.tools.impl.BelyListUserGroupsTool;
import gov.anl.aps.logr.rest.mcp.tools.impl.BelyListUsersTool;
import gov.anl.aps.logr.rest.mcp.tools.impl.BelySearchTool;
import io.swagger.v3.oas.annotations.Hidden;
import java.util.Base64;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import javax.ejb.EJB;
import javax.ws.rs.Consumes;
import javax.ws.rs.POST;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.Context;
import javax.ws.rs.core.HttpHeaders;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

/** Stateless MCP Streamable HTTP endpoint, revision {@code 2026-07-28} only, at a single POST {@code /api/mcp}. */
@Hidden
@Path("/mcp")
public class McpRoute {

    private static final Logger LOGGER = LogManager.getLogger(McpRoute.class.getName());

    private static final Pattern BASE64_SENTINEL = Pattern.compile("^=\\?base64\\?(.*)\\?=$");

    private static final McpToolRegistry REGISTRY = buildRegistry();

    @EJB
    DomainFacade domainFacade;
    @EJB
    ItemDomainLogbookFacade itemDomainLogbookFacade;
    @EJB
    ItemFacade itemFacade;
    @EJB
    UserInfoFacade userInfoFacade;
    @EJB
    UserGroupFacade userGroupFacade;

    private static McpToolRegistry buildRegistry() {
        McpToolRegistry registry = new McpToolRegistry();
        registry.register(new BelySearchTool());
        registry.register(new BelyListLogDocumentsTool());
        registry.register(new BelyGetLogDocumentTool());
        registry.register(new BelyListLogEntriesTool());
        registry.register(new BelyGetLogEntryTool());
        registry.register(new BelyListLookupsTool());
        registry.register(new BelyListUsersTool());
        registry.register(new BelyListUserGroupsTool());
        return registry;
    }

    @POST
    @Consumes(MediaType.WILDCARD)
    @Produces(MediaType.APPLICATION_JSON)
    public Response post(String body, @Context HttpHeaders headers) {
        if (!isEnabled()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        JsonNode id = null;
        try {
            String origin = headers.getHeaderString(McpConstants.HEADER_ORIGIN);
            if (origin != null && !isOriginAllowed(origin)) {
                throw new McpProtocolException(403, McpConstants.ERR_INVALID_REQUEST, "Origin not allowed: " + origin);
            }

            JsonNode root;
            try {
                root = McpConstants.MAPPER.readTree(body);
            } catch (JsonProcessingException e) {
                throw new McpProtocolException(400, McpConstants.ERR_PARSE_ERROR, "Malformed JSON: " + e.getOriginalMessage());
            }

            JsonRpcRequest request = JsonRpcRequest.parse(root);
            id = request.getId();

            validateHeaders(request, headers);

            UserInfo currentUser = resolveUser(headers);

            if (!request.hasId()) {
                return Response.status(Response.Status.ACCEPTED).build();
            }

            ObjectNode result = dispatch(request, currentUser);
            return Response.ok(JsonRpcResponse.success(id, result)).build();
        } catch (McpProtocolException e) {
            return Response.status(e.getHttpStatus())
                    .entity(JsonRpcResponse.error(id, e.toJsonRpcError()))
                    .build();
        } catch (Throwable t) {
            LOGGER.error("Unhandled error processing MCP request", t);
            return Response.ok(JsonRpcResponse.error(id,
                    new JsonRpcError(McpConstants.ERR_INTERNAL_ERROR, "Internal error")))
                    .build();
        }
    }

    private boolean isEnabled() {
        return Boolean.parseBoolean(ConfigurationUtility.getPortalProperty(McpConstants.PROP_ENABLED, "true"));
    }

    private boolean requiresAuth() {
        return Boolean.parseBoolean(ConfigurationUtility.getPortalProperty(McpConstants.PROP_REQUIRE_AUTH, "false"));
    }

    private boolean isOriginAllowed(String origin) {
        List<String> allowed = ConfigurationUtility.getPortalPropertyList(McpConstants.PROP_ALLOWED_ORIGINS);
        return allowed.contains(origin);
    }

    // Package-private (not private) so McpRouteHeaderValidationTest can call it directly, without a container.
    void validateHeaders(JsonRpcRequest request, HttpHeaders headers) throws McpProtocolException {
        String methodHeader = headers.getHeaderString(McpConstants.HEADER_METHOD);
        if (methodHeader == null || !methodHeader.equals(request.getMethod())) {
            throw new McpProtocolException(400, McpConstants.ERR_HEADER_MISMATCH,
                    "Mcp-Method header must equal the request \"method\"");
        }

        JsonNode params = request.getParams();
        JsonNode meta = params != null ? params.get("_meta") : null;
        JsonNode metaVersion = meta != null ? meta.get(McpConstants.META_PROTOCOL_VERSION) : null;
        if (metaVersion == null || !metaVersion.isTextual()) {
            throw new McpProtocolException(400, McpConstants.ERR_UNSUPPORTED_VERSION,
                    "params._meta[\"" + McpConstants.META_PROTOCOL_VERSION + "\"] is required; this server supports: "
                            + McpConstants.SUPPORTED_PROTOCOL_VERSIONS);
        }
        String requestedVersion = metaVersion.asText();

        String versionHeader = headers.getHeaderString(McpConstants.HEADER_PROTOCOL_VERSION);
        if (versionHeader == null || !versionHeader.equals(requestedVersion)) {
            throw new McpProtocolException(400, McpConstants.ERR_HEADER_MISMATCH,
                    "MCP-Protocol-Version header must equal params._meta[\"" + McpConstants.META_PROTOCOL_VERSION + "\"]");
        }

        if (!McpConstants.SUPPORTED_PROTOCOL_VERSIONS.contains(requestedVersion)) {
            ObjectNode data = McpConstants.MAPPER.createObjectNode();
            ArrayNode supported = data.putArray("supported");
            McpConstants.SUPPORTED_PROTOCOL_VERSIONS.forEach(supported::add);
            data.put("requested", requestedVersion);
            throw new McpProtocolException(400, McpConstants.ERR_UNSUPPORTED_VERSION,
                    "Unsupported protocol version: " + requestedVersion, data);
        }

        if ("tools/call".equals(request.getMethod())) {
            String nameHeader = headers.getHeaderString(McpConstants.HEADER_NAME);
            String paramsName = params != null && params.has("name") ? params.get("name").asText() : null;
            if (nameHeader == null || paramsName == null || !decodeSentinel(nameHeader).equals(paramsName)) {
                throw new McpProtocolException(400, McpConstants.ERR_HEADER_MISMATCH,
                        "Mcp-Name header must equal params.name");
            }
        }
    }

    // Decodes the =?base64?<b64>?= sentinel wrapper for non-ASCII header values; non-matching/invalid input passes through unchanged.
    static String decodeSentinel(String headerValue) {
        if (headerValue == null) {
            return null;
        }
        Matcher matcher = BASE64_SENTINEL.matcher(headerValue);
        if (!matcher.matches()) {
            return headerValue;
        }
        try {
            byte[] decoded = Base64.getDecoder().decode(matcher.group(1));
            return new String(decoded, java.nio.charset.StandardCharsets.UTF_8);
        } catch (IllegalArgumentException e) {
            return headerValue;
        }
    }

    private UserInfo resolveUser(HttpHeaders headers) throws McpProtocolException {
        String token = headers.getHeaderString(McpConstants.HEADER_TOKEN);
        if (token == null || token.isEmpty()) {
            if (requiresAuth()) {
                throw new McpProtocolException(401, McpConstants.ERR_UNAUTHORIZED, "Authentication required");
            }
            return null;
        }

        UserSessionKeeper keeper = UserSessionKeeper.getInstance();
        if (!keeper.validateToken(token)) {
            throw new McpProtocolException(401, McpConstants.ERR_UNAUTHORIZED, "Invalid or expired token");
        }
        User user = keeper.getUserForToken(token);
        return user != null ? user.getUser() : null;
    }

    private ObjectNode dispatch(JsonRpcRequest request, UserInfo currentUser) throws McpProtocolException {
        switch (request.getMethod()) {
            case "server/discover":
                return discover();
            case "tools/list":
                return listTools();
            case "tools/call":
                return callTool(request, currentUser);
            case "initialize":
                throw new McpProtocolException(400, McpConstants.ERR_UNSUPPORTED_VERSION,
                        "This server implements MCP revision " + McpConstants.PROTOCOL_VERSION
                                + " only (stateless — no \"initialize\" handshake). Supported versions: "
                                + McpConstants.SUPPORTED_PROTOCOL_VERSIONS);
            default:
                throw new McpProtocolException(404, McpConstants.ERR_METHOD_NOT_FOUND, "Method not found: " + request.getMethod());
        }
    }

    private ObjectNode discover() {
        ObjectNode result = McpConstants.MAPPER.createObjectNode();
        result.put("resultType", "complete");
        result.put("protocolVersion", McpConstants.PROTOCOL_VERSION);
        ArrayNode supported = result.putArray("supportedProtocolVersions");
        McpConstants.SUPPORTED_PROTOCOL_VERSIONS.forEach(supported::add);

        ObjectNode serverInfo = result.putObject("serverInfo");
        serverInfo.put("name", McpConstants.SERVER_NAME);
        serverInfo.put("title", McpConstants.SERVER_TITLE);
        serverInfo.put("version", McpConstants.SERVER_VERSION);

        ObjectNode capabilities = result.putObject("capabilities");
        ObjectNode toolsCapability = capabilities.putObject("tools");
        toolsCapability.put("listChanged", false);

        result.put("instructions", McpConstants.INSTRUCTIONS);
        return result;
    }

    private ObjectNode listTools() {
        ObjectNode result = McpConstants.MAPPER.createObjectNode();
        result.put("resultType", "complete");
        ArrayNode tools = result.putArray("tools");
        for (McpTool tool : REGISTRY.list()) {
            ObjectNode toolNode = tools.addObject();
            toolNode.put("name", tool.getName());
            toolNode.put("title", tool.getTitle());
            toolNode.put("description", tool.getDescription());
            toolNode.set("inputSchema", tool.getInputSchema());
        }
        return result;
    }

    private ObjectNode callTool(JsonRpcRequest request, UserInfo currentUser) throws McpProtocolException {
        // -32602 answers with HTTP 200, same as -32603 below: some clients never surface a non-2xx body to the model.
        JsonNode params = request.getParams();
        String name = params != null && params.has("name") ? params.get("name").asText() : null;
        if (name == null) {
            throw new McpProtocolException(200, McpConstants.ERR_INVALID_PARAMS, "Missing params.name");
        }

        McpTool tool = REGISTRY.get(name);
        if (tool == null) {
            throw new McpProtocolException(200, McpConstants.ERR_INVALID_PARAMS, "Unknown tool: " + name);
        }

        JsonNode arguments = params.has("arguments") ? params.get("arguments") : null;
        McpToolContext ctx = new McpToolContext(
                domainFacade, itemDomainLogbookFacade, itemFacade, userInfoFacade, userGroupFacade, currentUser);

        McpToolResult result;
        try {
            result = tool.call(arguments, ctx);
        } catch (McpArgumentException e) {
            throw new McpProtocolException(200, McpConstants.ERR_INVALID_PARAMS, e.getMessage());
        }

        return result.toJson();
    }
}
