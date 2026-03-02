/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.utilities;

import gov.anl.aps.logr.common.exceptions.CdbException;
import gov.anl.aps.logr.common.mqtt.model.LogReactionEvent;
import gov.anl.aps.logr.portal.model.db.beans.LogFacade;
import gov.anl.aps.logr.portal.model.db.beans.LogReactionFacade;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import gov.anl.aps.logr.portal.model.db.entities.LogReaction;
import gov.anl.aps.logr.portal.model.db.entities.Reaction;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import java.util.List;

/**
 *
 * @author djarosz
 */
public class LogReactionControllerUtility extends CdbEntityControllerUtility<LogReaction, LogReactionFacade> {

    LogReactionFacade logReactionFacade;
    LogFacade logFacade;

    public LogReactionControllerUtility() {
        logReactionFacade = LogReactionFacade.getInstance();
        logFacade = LogFacade.getInstance();
    }

    @Override
    protected LogReactionFacade getEntityDbFacade() {
        return logReactionFacade;
    }

    @Override
    public LogReaction createEntityInstance(UserInfo sessionUser) {
        LogReaction lr = new LogReaction();
        lr.setUserInfo(sessionUser);
        return lr;
    }

    @Override
    public String getEntityTypeName() {
        return "Log Reaction";
    }

    public void toggleReaction(Log entry, Reaction reaction, UserInfo user) throws CdbException {
        // Fetch the latest version
        entry = logFacade.find(entry.getId());

        List<LogReaction> logReactionList = entry.getLogReactionList();
        LogReaction dbReaction = null;

        // Check if need to remove log reaction.
        for (LogReaction lr : logReactionList) {
            UserInfo userId = lr.getUserInfo();

            if (user.equals(userId)) {
                Reaction existingReaction = lr.getReaction();

                if (existingReaction.equals(reaction)) {
                    dbReaction = lr;
                    break;
                }
            }
        }

        ItemDomainLogbook parentLogDoc = ItemDomainLogbookControllerUtility.getParentLogDocument(entry);

        if (dbReaction != null) {
            dbReaction.addActionEvent(new LogReactionEvent(dbReaction,
                    entry,
                    parentLogDoc,
                    user,
                    "User removed a reaction",
                    true));
            logReactionList.remove(dbReaction);
            destroy(dbReaction, user);
        } else {
            LogReaction lr = createEntityInstance(user);
            lr.setLog(entry);
            lr.setReaction(reaction);
            lr.addActionEvent(new LogReactionEvent(lr,
                    entry,
                    parentLogDoc,
                    user,
                    "User added a reaction",
                    false));
            create(lr, user);
        }

    }

}
