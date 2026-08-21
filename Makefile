# Copyright (c) UChicago Argonne, LLC. All rights reserved.
# See LICENSE file.

# The top level makefile. Targets like "all" and "clean"
# are defined in the RULES file.

TOP = .
#SUBDIRS = irmis src
SUBDIRS = src

.PHONY: help
.PHONY: support support-mysql dev-config
.PHONY: db backup db-dev deploy-web-portal undeploy-web-portal deploy-web-service undeploy-web-service
.PHONY: db-dev backup-dev deploy-web-portal-dev undeploy-web-portal-dev deploy-web-service-dev undeploy-web-service-dev
.PHONY: prepare-release release-python-client

default:

help:
	@echo "BELY - available make targets"
	@echo ""
	@echo "Setup:"
	@echo "  support               Install support software (Java, Payara, MySQL, etc.)"
	@echo "  support-portal        Install support software for the web portal only"
	@echo "  support-mysql         Install MySQL and deploy mysqld"
	@echo "  support-netbeans      Install NetBeans IDE"
	@echo "  dev-config            Create development configuration"
	@echo "  configuration         Create deployment configuration"
	@echo "  prepare-dev-env       support + db + dev-config"
	@echo ""
	@echo "Database:"
	@echo "  clean-db              Create a clean database with schema"
	@echo "  test-db               Create a test database with test data"
	@echo "  db                    Create the database (interactive)"
	@echo "  backup                Backup the database"
	@echo ""
	@echo "Build & Deploy:"
	@echo "  configure-web-portal  Configure the web portal"
	@echo "  deploy-web-portal     Deploy the web portal"
	@echo "  deploy-web-service    Deploy the web service"
	@echo "  deploy-cdb-plugin     Deploy a BELY plugin"
	@echo "  unconfigure-web-portal  Unconfigure the web portal"
	@echo "  undeploy-web-portal   Undeploy the web portal"
	@echo "  undeploy-web-service  Undeploy the web service"
	@echo ""
	@echo "Testing:"
	@echo "  test                  Run the full test suite (backs up DB, deploys test DB,"
	@echo "                        runs tests, restores DB)"
	@echo "  test-plugins          Run plugin utility tests"
	@echo ""
	@echo "Release:"
	@echo "  prepare-release       Bump the version across the repo and scaffold release notes"
	@echo "  release-python-client Build and publish bely-api, bely-cli, and"
	@echo "                        bely-mqtt-framework to PyPI"
	@echo ""
	@echo "Development variants:"
	@echo "  Most Setup/Database/Build & Deploy targets above have a '-dev' counterpart"
	@echo "  (e.g. db-dev, backup-dev, deploy-web-portal-dev) that operates against the"
	@echo "  dev configuration/database instead of the production one."

prepare-release:
	$(TOP)/sbin/bely_prepare_release.py

release-python-client:
	$(TOP)/sbin/bely_release_pip.py

prepare-dev-env: support db dev-config

dev-config:
	$(TOP)/sbin/cdb_prepare_dev_config.sh

configuration:
	$(TOP)/sbin/cdb_create_configuration.sh

support:
	$(TOP)/sbin/cdb_install_support.sh

support-portal:
	$(TOP)/sbin/cdb_install_support_portal.sh

support-mysql:
	$(TOP)/sbin/cdb_install_support_mysql.sh && $(TOP)/sbin/cdb_deploy_mysqld.sh

support-netbeans:
	$(TOP)/sbin/cdb_install_support_netbeans.sh

clean-db:
	$(TOP)/sbin/cdb_create_db.sh logr $(TOP)/db/sql/clean

test-db:
	$(TOP)/sbin/cdb_create_db.sh logr $(TOP)/db/sql/test

test:
	$(TOP)/sbin/cdb_test.sh

test-plugins:
	cd $(TOP)/tools/developer_tools/logr_plugins && python -m pytest test/ -v

db:
	$(TOP)/sbin/cdb_create_db.sh

backup:
	$(TOP)/sbin/cdb_backup_all.sh logr

configure-web-portal: dist
	$(TOP)/sbin/cdb_configure_web_portal.sh

deploy-cdb-plugin:
	$(TOP)/tools/developer_tools/logr_plugins/deploy_plugin.py bely

deploy-web-portal: dist
	$(TOP)/sbin/cdb_deploy_web_portal.sh

deploy-web-service:
	$(TOP)/sbin/cdb_deploy_web_service.sh

unconfigure-web-portal:
	$(TOP)/sbin/cdb_unconfigure_web_portal.sh

undeploy-web-portal:
	$(TOP)/sbin/cdb_undeploy_web_portal.sh

undeploy-web-service:
	$(TOP)/sbin/cdb_undeploy_web_service.sh

configuration-dev:
	$(TOP)/sbin/cdb_create_configuration.sh cdb_dev

db-dev:
	$(TOP)/sbin/cdb_create_db.sh logr_dev

clean-db-dev:
	$(TOP)/sbin/cdb_create_db.sh logr_dev $(TOP)/db/sql/clean

backup-dev:
	$(TOP)/sbin/cdb_backup_all.sh logr_dev

deploy-cdb-plugin-dev:
	$(TOP)/tools/developer_tools/logr_plugins/deploy_plugin.py cdb_dev

deploy-web-portal-dev: dist 
	$(TOP)/sbin/cdb_deploy_web_portal.sh cdb_dev Dev

configure-web-portal-dev: dist
	$(TOP)/sbin/cdb_configure_web_portal.sh cdb_dev

deploy-web-service-dev:
	$(TOP)/sbin/cdb_deploy_web_service.sh cdb_dev

unconfigure-web-portal-dev:
	$(TOP)/sbin/cdb_unconfigure_web_portal.sh cdb_dev

undeploy-web-portal-dev:
	$(TOP)/sbin/cdb_undeploy_web_portal.sh cdb_dev

undeploy-web-service-dev:
	$(TOP)/sbin/cdb_undeploy_web_service.sh cdb_dev

include $(TOP)/tools/make/RULES_CDB
