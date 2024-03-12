/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers;

import gov.anl.aps.logr.common.constants.CdbRole;
import gov.anl.aps.logr.portal.model.db.beans.UserInfoFacade;
import gov.anl.aps.logr.portal.model.db.entities.EntityInfo;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import gov.anl.aps.logr.portal.utilities.AuthorizationUtility;
import gov.anl.aps.logr.portal.utilities.ConfigurationUtility;
import gov.anl.aps.logr.common.utilities.LdapUtility;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import gov.anl.aps.logr.common.utilities.CryptUtility;
import gov.anl.aps.logr.portal.constants.SystemLogLevel;
import gov.anl.aps.logr.portal.model.db.beans.UserSessionFacade;
import gov.anl.aps.logr.portal.model.db.entities.UserSession;
import gov.anl.aps.logr.portal.model.db.utilities.LogUtility;
import java.io.Serializable;
import java.time.Duration;
import java.time.Instant;
import java.util.Date;
import java.util.List;
import javax.ejb.EJB;
import javax.enterprise.context.SessionScoped;
import javax.inject.Named;
import javax.servlet.http.HttpSession;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

/**
 * Login controller.
 */
@Named("loginController")
@SessionScoped
public class LoginController implements Serializable {

    private static final int MilisecondsInSecond = 1000;
    private static final int SessionTimeoutDecreaseInSeconds = 10;

    // Whenever a session is saved it will get updated with the offset. 
    // 7 day offset
    private static final int SESSION_EXPIRATION_OFFSET = 604800;

    @EJB
    private UserInfoFacade userFacade;

    @EJB
    private UserSessionFacade userSessionFacade;

    private String username = null;
    private String password = null;
    private boolean loggedInAsAdmin = false;
    private boolean loggedInAsMaintainer = false;
    private boolean loggedInAsAdvancedUser = false;
    private boolean loggedInAsUser = false;
    private boolean checkedSession = false;
    private boolean registeredSession = false;
    private UserInfo user = null;
    private Integer sessionTimeoutInMiliseconds = null;

    private SettingController settingController = null;
    private final String SETTING_CONTROLLER_NAME = "settingController";

    private static final String AdminGroupListPropertyName = "cdb.portal.adminGroupList";
    private static final String MaintainerGroupListPropertyName = "cdb.portal.maintainerGroupList";
    private static final String AdvancedGroupListPropertyName = "cdb.portal.advancedGroupList";
    private static final List<String> maintainerGroupNameList = ConfigurationUtility.getPortalPropertyList(MaintainerGroupListPropertyName);
    private static final List<String> advancedGroupNameList = ConfigurationUtility.getPortalPropertyList(AdvancedGroupListPropertyName);
    private static final List<String> adminGroupNameList = ConfigurationUtility.getPortalPropertyList(AdminGroupListPropertyName);
    private static final Logger logger = LogManager.getLogger(LoginController.class.getName());

    public LoginController() {
    }

    public static LoginController getInstance() {
        return (LoginController) SessionUtility.findBean("loginController");
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    /**
     * Function used to ensure user stays logged in after a session reset.
     */
    public void preRenderLogin() {
        isLoggedIn();
    }

    public boolean isLoggedIn() {
        if (!checkedSession) {
            checkedSession = true;
            String sessionKey = SessionUtility.getSessionCookie();
            if (sessionKey != null) {
                UserSession session = userSessionFacade.findBySessionKey(sessionKey);

                if (session != null) {
                    user = session.getUserInfo();
                    username = user.getUsername();
                    loadAuthenticatedUser(true, session);
                }
            }

        }
        return (loggedInAsAdmin || loggedInAsUser || loggedInAsMaintainer || loggedInAsAdvancedUser);
    }

    public boolean isLoggedInForImport() {
        return (loggedInAsAdmin || loggedInAsMaintainer || loggedInAsAdvancedUser);
    }

    public boolean isLoggedInAsAdmin() {
        return loggedInAsAdmin;
    }

    public void setLoggedInAsAdmin(boolean loggedInAsAdmin) {
        this.loggedInAsAdmin = loggedInAsAdmin;
    }

    public boolean isLoggedInAsAdvancedUser() {
        return loggedInAsAdvancedUser;
    }

    public void setLoggedInAsAdvancedUser(boolean loggedInAsAdvancedUser) {
        this.loggedInAsAdvancedUser = loggedInAsAdvancedUser;
    }

    public boolean isLoggedInAsMaintainer() {
        return loggedInAsMaintainer;
    }

    public void setLoggedInAsMaintainer(boolean loggedInAsMaintainer) {
        this.loggedInAsMaintainer = loggedInAsMaintainer;
    }

    public boolean isLoggedInAsUser() {
        return loggedInAsUser;
    }

    public void setLoggedInAsUser(boolean loggedInAsUser) {
        this.loggedInAsUser = loggedInAsUser;
    }

    private boolean isAdmin(String username) {
        return isAdmin(username, userFacade);
    }

    private boolean isMaintainer(String username) {
        return isMaintainer(username, userFacade);
    }

    private boolean isAdvanced(String username) {
        return isAdvanced(username, userFacade);
    }

    public static boolean isAdmin(String username, UserInfoFacade userFacade) {
        UserInfo findByUsername = userFacade.findByUsername(username);
        if (findByUsername != null) {
            return findByUsername.isUserAdmin();
        }
        return false;
    }

    public static boolean isMaintainer(String username, UserInfoFacade userFacade) {
        UserInfo findByUsername = userFacade.findByUsername(username);
        if (findByUsername != null) {
            return findByUsername.isUserMaintainer();
        }
        return false;
    }

    public static boolean isAdvanced(String username, UserInfoFacade userFacade) {
        UserInfo findByUsername = userFacade.findByUsername(username);
        if (findByUsername != null) {
            return findByUsername.isUserAdvanced();
        }
        return false;
    }

    /**
     * Login action.
     *
     * @return URL to home page if login is successful, or null in case of
     * errors
     */
    public String login() {
        loggedInAsAdmin = false;
        loggedInAsUser = false;
        if (username == null || password == null || username.isEmpty() || password.isEmpty()) {
            SessionUtility.addWarningMessage("Incomplete Input", "Please enter both username and password.");
            return (username = password = null);
        }

        user = userFacade.findByUsername(username);
        if (user == null) {
            SessionUtility.addErrorMessage("Unknown User", "Username " + username + " is not registered.");
            LogUtility.addSystemLog(SystemLogLevel.loginWarning, "Non-registered user login attempt: " + username);
            return (username = password = null);
        }

        boolean isAdminUser = isAdmin(username);
        logger.debug("User " + username + " is admin: " + isAdminUser);

        if (validateCredentials(user, password)) {
            loadAuthenticatedUser();
            return reloadPage();
        } else {
            SessionUtility.addErrorMessage("Invalid Credentials", "Username/password combination could not be verified.");
            LogUtility.addSystemLog(SystemLogLevel.loginWarning, "Authentication Failed: " + username);
            return (username = password = null);
        }

    }

    public static boolean validateCredentials(UserInfo user, String password) {
        String username = user.getUsername();
        boolean validCredentials = false;
        if (user.getPassword() != null && CryptUtility.verifyPasswordWithPbkdf2(password, user.getPassword())) {
            logger.debug("User " + username + " is authorized by CDB");
            validCredentials = true;
        } else if (LdapUtility.validateCredentials(username, password)) {
            logger.debug("User " + username + " is authorized by LDAP");
            validCredentials = true;
        } else {
            logger.debug("User " + username + " is not authorized");
        }
        return validCredentials;
    }

    private Date generateSessionExpiration(long expirationSecondOffset) {
        Date now = new Date();
        Instant future = now.toInstant();
        future = future.plus(Duration.ofSeconds(expirationSecondOffset));

        return Date.from(future);
    }

    private void saveSession(UserSession session) {
        if (session.getId() == null) {
            userSessionFacade.create(session);
        } else {
            userSessionFacade.edit(session);
        }

    }

    private void loadAuthenticatedUser() {
        loadAuthenticatedUser(false, null);
    }

    private void loadAuthenticatedUser(boolean quiet, UserSession userSession) {
        if (settingController == null) {
            settingController = (SettingController) SessionUtility.findBean(SETTING_CONTROLLER_NAME);
        }
        settingController.loadSessionUser(user);

        refreshToken(userSession);
        SessionUtility.setUser(user);

        boolean isAdminUser = isAdmin(username);
        boolean isMaintainer = isMaintainer(username);
        boolean isAdvanced = isAdvanced(username);
        if (isAdminUser) {
            loggedInAsAdmin = true;
            SessionUtility.setRole(CdbRole.ADMIN);
            if (!quiet) {
                SessionUtility.addInfoMessage("Successful Login", "Administrator " + username + " is logged in.");
            }
        } else if (isMaintainer) {
            loggedInAsMaintainer = true;
            SessionUtility.setRole(CdbRole.MAINTAINER);
            if (!quiet) {
                SessionUtility.addInfoMessage("Successful Login", "Maintainer " + username + " is logged in.");
            }
        } else if (isAdvanced) {
            loggedInAsAdvancedUser = true;
            SessionUtility.setRole(CdbRole.ADVANCED);
            if (!quiet) {
                SessionUtility.addInfoMessage("Successful Login", "Advanced user " + username + " is logged in.");
            }
        } else {
            loggedInAsUser = true;
            SessionUtility.setRole(CdbRole.USER);
            if (!quiet) {
                SessionUtility.addInfoMessage("Successful Login", "User " + username + " is logged in.");
            }
        }
        LogUtility.addSystemLog(SystemLogLevel.loginInfo, "Authentication Succeeded: " + username);
    }

    public void refreshToken() {
        String sessionKey = SessionUtility.getSessionCookie();
        if (sessionKey != null) {
            UserSession session = userSessionFacade.findBySessionKey(sessionKey);

            if (session != null) {
                refreshToken(session); 
            }
        }
    }

    private void refreshToken(UserSession userSession) {
        String token;
        if (userSession != null) {
            token = userSession.getSessionKey();
        } else {
            token = CryptUtility.generateSessionToken(); 
            String remoteAddress = SessionUtility.getRemoteAddress();

            userSession = new UserSession();
            userSession.setSessionKey(token);
            userSession.setUserInfo(user);
            userSession.setSessionName(remoteAddress);
        }

        Date expiration = generateSessionExpiration(SESSION_EXPIRATION_OFFSET);
        userSession.setExpirationDateTime(expiration);
        saveSession(userSession);
        SessionUtility.setSessionCookie(token, SESSION_EXPIRATION_OFFSET);
    }

    public String reloadPage() {
        String landingPage = SessionUtility.getRedirectToCurrentViewWithHandlerTransfer();
        if (landingPage.contains("login")) {
            landingPage = SessionUtility.popViewFromStack();
            if (landingPage == null) {
                landingPage = "/index";
            }

            landingPage = SessionUtility.addRedirectToViewId(landingPage);
        }

        logger.debug("Landing page: " + landingPage);
        return landingPage;
    }

    public String dropMaintainerRole() {
        loggedInAsAdmin = false;
        loggedInAsMaintainer = false;
        loggedInAsUser = true;
        SessionUtility.setRole(CdbRole.USER);
        settingController.resetSessionVariables();
        return reloadPage();
    }

    public String dropAdminRole() {
        loggedInAsAdmin = false;
        loggedInAsMaintainer = false;
        loggedInAsUser = true;
        SessionUtility.setRole(CdbRole.USER);
        settingController.resetSessionVariables();
        return reloadPage();
    }

    public String displayUsername() {
        if (isLoggedIn()) {
            return username;
        } else {
            return "Not Logged In";
        }
    }

    public String displayRole() {
        if (isLoggedInAsAdmin()) {
            return "Administrator";
        } else if (isLoggedInAsMaintainer()) {
            return "Maintainer";
        } else if (isLoggedInAsAdvancedUser()) {
            return "Advanced user";
        } else {
            return "User";
        }
    }

    public boolean isEntityWriteable(EntityInfo entityInfo) {
        // If user is not logged in, object is not writeable
        if (!isLoggedIn()) {
            return false;
        }

        if (entityInfo == null) {
            return false;
        }

        // Admins can write any object.
        if (isLoggedInAsAdmin()) {
            return true;
        }

        if (isLoggedInAsMaintainer()) {
            return true;
        }

        return AuthorizationUtility.isEntityWriteableByUser(entityInfo, user);

    }

    public boolean isUserWriteable(UserInfo user) {
        if (!isLoggedIn()) {
            return false;
        }
        return isLoggedInAsAdmin() || this.user.getId() == user.getId();
    }

    private void resetLoginInfo() {
        loggedInAsAdmin = false;
        loggedInAsUser = false;
        user = null;
    }

    public void handleInvalidSessionRequest() {
        SessionUtility.addWarningMessage("Warning", "Invalid session request");
        SessionUtility.navigateTo("/views/index?faces-redirect=true");
    }

    public void removeSession(UserSession session) {
        userSessionFacade.remove(session);
    }

    /**
     * Logout action.
     *
     * @return URL to home page
     */
    public String logout() {
        logger.debug("Logging out user: " + user);
        SessionUtility.clearSession();
        SessionUtility.invalidateSession();
        SessionUtility.setSessionCookie(null, 0);
        resetLoginInfo();

        // Remove session upon logout. 
        String sessionKey = SessionUtility.getSessionCookie();
        if (sessionKey != null) {
            UserSession session = userSessionFacade.findBySessionKey(sessionKey);
            if (session != null) {
                removeSession(session);
            }
        }

        return "/index?faces-redirect=true";
    }

    public String resetSession() {
        String currentUsername = null;
        if (isLoggedIn()) {
            currentUsername = user.getUsername();
        }

        SessionUtility.clearSession();

        return "/index?faces-redirect=true";
    }

    public void sessionIdleListener() {
        String msg = "Session expired ";
        if (user != null) {
            msg += "for user " + user;
        } else {
            msg += "for anonymous user";
        }
        SessionUtility.invalidateSession();
        SessionUtility.addWarningMessage("Warning", msg);
        logger.debug(msg);
    }

    public int getSessionTimeoutInMiliseconds() {
        if (sessionTimeoutInMiliseconds == null) {
            int timeoutInSeconds = SessionUtility.getSessionTimeoutInSeconds();
            logger.debug("Session timeout in seconds: " + timeoutInSeconds);
            // reduce configured value slightly to avoid premature session expiration issues
            sessionTimeoutInMiliseconds = (timeoutInSeconds - SessionTimeoutDecreaseInSeconds) * MilisecondsInSecond;
        }
        // logger.debug("Idle timeout in miliseconds: " + sessionTimeoutInMiliseconds);
        return sessionTimeoutInMiliseconds;
    }

    public void registerSession() {
        if (!registeredSession) {
            registeredSession = true;
            SessionController instance = SessionController.getInstance();
            HttpSession currentSession = SessionUtility.getCurrentSession();
            instance.registerSession(currentSession);
        }

    }

    public boolean isRegisteredSession() {
        return registeredSession;
    }

    public static List<String> getAdminGroupNameList() {
        return adminGroupNameList;
    }

    public static List<String> getAdvancedGroupNameList() {
        return advancedGroupNameList;
    }

    public static List<String> getMaintainerGroupNameList() {
        return maintainerGroupNameList;
    }
}
