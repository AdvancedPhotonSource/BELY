# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BELY (Best Electronic Logbook Yet) is a Java EE web application for electronic logbook management. It is deployed on Payara Server (GlassFish fork) and uses MySQL/MariaDB as its database. The project includes:

- **LogrPortal**: Main Java EE web application (JSF/PrimeFaces frontend + REST API)
- **Python web service**: Python-based web service components
- **MQTT integration**: Python framework for handling MQTT events and notifications
- **CLI utilities**: Command-line tools for searching and querying the system

## Build and Development Commands

### Environment Setup

Always source the environment setup script before running any commands:
```bash
source setup.sh
```

This sets up critical environment variables:
- `LOGR_ROOT_DIR`: Root directory of the repository
- `LOGR_SUPPORT_DIR`: Support software directory (Payara, Java, MySQL, etc.)
- `LOGR_INSTALL_DIR`: Installation directory
- `LOGR_DATA_DIR`: Data directory
- `PYTHONPATH`: Includes `src/python` and Python client paths

### Initial Setup

```bash
# Install support software (Java, Payara, etc.)
make support

# Install MySQL (if needed)
make support-mysql

# Install NetBeans IDE
make support-netbeans

# Create development configuration
make dev-config
```

### Database Management

```bash
# Create clean database with schema
make clean-db

# Create test database with test data
make test-db

# Backup database
make backup

# Development database variants
make clean-db-dev
make backup-dev
```

Database SQL files are located in `db/sql/`:
- `clean/`: Clean database schema initialization scripts
- `test/`: Test data initialization scripts
- `static/`: Static lookup data (e.g., notification providers)
- `updates/`: Database migration scripts (e.g., `updateTo2025.3.sql`)
- `create_logr_tables.sql`: Main table creation script
- `create_stored_procedures.sql`: Stored procedures
- `create_views.sql`: Database views

### Building and Deployment

```bash
# Build the web portal
cd src/java/LogrPortal
ant clean
ant dist

# Deploy to Payara (from project root)
make deploy-web-portal

# Deploy web service
make deploy-web-service

# Undeploy
make undeploy-web-portal
make undeploy-web-service

# Development deployment variants
make deploy-web-portal-dev
make deploy-web-service-dev
```

### Running Tests

```bash
# Run full test suite (backs up DB, deploys test DB, runs tests, restores DB)
make test

# Manual API tests
cd tools/developer_tools/python-client/
pytest test/api_test.py

# Test requirements
pip install -r tools/developer_tools/python-client/test/requirements.txt
```

### Python Web Service Development

```bash
# Start the Python web service
./sbin/cdbWebService.sh
```

Python code is in `src/python/cdb/`.

## Architecture

### Java Package Structure

All Java code is under `src/java/LogrPortal/src/java/gov/anl/aps/logr/`:

**portal** - Main web portal application
- `controllers/` - JSF managed beans for UI logic
- `model/db/entities/` - JPA entity classes (e.g., `Log`, `UserInfo`, `NotificationConfiguration`)
- `model/db/beans/` - EJB facades for database operations (stateless session beans)
- `view/` - View objects and JSF utilities
- `import_export/` - Import/export functionality
- `plugins/` - Plugin support system
- `utilities/` - General utility classes

**rest** - REST API
- `routes/` - JAX-RS resource classes (e.g., `LogbookRoute`, `SearchRoute`)
- `authentication/` - Authentication filters and utilities
- `entities/` - DTO classes for API responses
- `provider/` - JAX-RS providers

**common** - Shared utilities
- `mqtt/` - MQTT integration models and utilities
- `objects/` - Common data objects
- `utilities/` - Shared utility classes
- `search/` - Search functionality

**api** - API client interfaces

### Web Application Structure

Location: `src/java/LogrPortal/web/`

- `views/` - XHTML pages organized by entity type (e.g., `log/`, `userInfo/`, `notificationConfiguration/`)
- `templates/` - XHTML template files
- `resources/` - Static resources (CSS, JavaScript, images)
- `WEB-INF/` - Web application configuration

### Technology Stack

- **Framework**: Java EE 8 (JSF 2.3, EJB 3.2, JPA 2.2, JAX-RS 2.1)
- **UI**: PrimeFaces 11 + PrimeFaces Extensions, OmniFaces 3
- **App Server**: Payara 5.2022.5 (GlassFish fork)
- **Database**: MySQL/MariaDB (driver: mariadb-java-client-3.1.0.jar)
- **ORM**: EclipseLink (JPA implementation)
- **Build**: Apache Ant + NetBeans project
- **API Docs**: Swagger/OpenAPI 2.1.5
- **PDF Generation**: iText 5.5.13.1
- **Markdown**: Flexmark 0.64.8
- **Logging**: Log4j 2.17.0

### MQTT Integration

The MQTT notification framework is a pluggable Python system for handling MQTT events:
- Location: `tools/developer_tools/bely-mqtt-message-broker/`
- Features: Type-safe Pydantic models, topic matching with wildcards, notification handlers (email, Slack, Discord)
- See `tools/developer_tools/bely-mqtt-message-broker/README.md` for details

### Plugins System

BELY supports custom plugins for extending functionality:
- Templates: `tools/developer_tools/logr_plugins/pluginTemplates/`
- Deployment: `make deploy-cdb-plugin` or `make deploy-cdb-plugin-dev`

## Development Workflow

### NetBeans Setup

1. Open NetBeans: `netbeans &`
2. File > Open Project > Select `src/java/LogrPortal`
3. Resolve missing server: Right-click project > "Resolve Missing Server Problem"
4. Add Payara Server pointing to `$LOGR_SUPPORT_DIR/netbeans/payara`
5. Copy MariaDB driver to Payara:
   ```bash
   cp src/java/LogrPortal/lib/mariadb-java-client-3.1.0.jar \
      $LOGR_SUPPORT_DIR/netbeans/payara/glassfish/domains/domain1/lib/
   ```
6. Run project from NetBeans

### Adding New Entities

When adding new database entities (e.g., notification system):

1. Update `db/sql/create_logr_tables.sql` with new table definitions
2. Add static data SQL files to `db/sql/static/` if needed
3. Create JPA `@Entity` class in `portal/model/db/entities/`
4. Create `@Stateless` facade in `portal/model/db/beans/` (extends `AbstractFacade`)
5. Create JSF controller in `portal/controllers/` (extends appropriate base controller)
6. Create XHTML views in `web/views/<entity_name>/`
7. Update database with `make clean-db` or create migration in `db/sql/updates/`

### Database Migrations

Version updates go in `db/sql/updates/updateToYYYY.X.sql` (e.g., `updateTo2025.3.sql`)

## Key Patterns

- **Entity/Facade/Controller**: Standard Java EE pattern - JPA entities, EJB facades for CRUD, JSF controllers for UI
- **Named Queries**: Use JPA `@NamedQuery` annotations on entities for common queries
- **Lazy Loading**: JSF data tables use lazy loading models
- **Session Management**: Session-scoped JSF beans maintain user state
- **REST Authentication**: Token-based auth via `rest/authentication/`
- **MQTT Events**: Notification configurations trigger MQTT messages handled by Python framework

## Important Files

- `Makefile`: Top-level make targets for building, deploying, testing
- `setup.sh`: Environment variable setup (must be sourced)
- `sbin/`: Deployment and utility scripts
- `src/java/LogrPortal/build.xml`: Ant build file
- `src/java/LogrPortal/nbproject/project.properties`: NetBeans project configuration
- `db/sql/create_logr_tables.sql`: Main database schema

## Notes

- The project is also known as "ComponentDB" or "CDB" in some contexts
- Default database name: `logr` (development: `logr_dev`)
- Application URL after deployment: `https://<hostname>:8181/bely` or `https://<hostname>:8181/cdb`
- The main branch is `master` (not `main`)
- Always run database operations and deployments from the repository root after sourcing `setup.sh`
