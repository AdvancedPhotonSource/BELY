/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.routes;

import gov.anl.aps.logr.common.exceptions.AuthenticationError;
import gov.anl.aps.logr.portal.model.db.beans.UserInfoFacade;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import java.lang.reflect.Field;

/** Regression test for REST login by an unknown user. */
public class AuthenticationRouteTest {

    public static void main(String[] args) throws Exception {
        AuthenticationRoute route = new AuthenticationRoute();
        Field userFacade = AuthenticationRoute.class.getDeclaredField("userFacade");
        userFacade.setAccessible(true);
        userFacade.set(route, new UnknownUserFacade());

        try {
            route.authenticateUser("unknown-user", "password");
            throw new AssertionError("Expected authentication to fail");
        } catch (AuthenticationError ex) {
            if (!"Could not verify username or password.".equals(ex.getMessage())) {
                throw new AssertionError("Unexpected authentication error: " + ex.getMessage());
            }
        }

        System.out.println("PASS unknown user returns authentication error");
    }

    private static class UnknownUserFacade extends UserInfoFacade {
        @Override
        public UserInfo findByUsername(String username) {
            return null;
        }
    }
}
