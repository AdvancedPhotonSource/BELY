/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.entities;

import java.io.Serializable;
import javax.persistence.Basic;
import javax.persistence.Column;
import javax.persistence.Embeddable;
import javax.validation.constraints.NotNull;

/**
 * Log Reaction PK entity class represents the log_reaction primary key of log reaction database table.
 *
 * @author djarosz
 */
@Embeddable
public class LogReactionPK implements Serializable {

    @Basic(optional = false)
    @NotNull
    @Column(name = "log_id")
    private int logId;
    @Basic(optional = false)
    @NotNull
    @Column(name = "reaction_id")
    private int reactionId;
    @Basic(optional = false)
    @NotNull
    @Column(name = "user_id")
    private int userId;

    public LogReactionPK() {
    }

    public LogReactionPK(int logId, int reactionId, int userId) {
        this.logId = logId;
        this.reactionId = reactionId;
        this.userId = userId;
    }

    public int getLogId() {
        return logId;
    }

    public void setLogId(int logId) {
        this.logId = logId;
    }

    public int getReactionId() {
        return reactionId;
    }

    public void setReactionId(int reactionId) {
        this.reactionId = reactionId;
    }

    public int getUserId() {
        return userId;
    }

    public void setUserId(int userId) {
        this.userId = userId;
    }

    @Override
    public int hashCode() {
        int hash = 0;
        hash += (int) logId;
        hash += (int) reactionId;
        hash += (int) userId;
        return hash;
    }

    @Override
    public boolean equals(Object object) {
        // TODO: Warning - this method won't work in the case the id fields are not set
        if (!(object instanceof LogReactionPK)) {
            return false;
        }
        LogReactionPK other = (LogReactionPK) object;
        if (this.logId != other.logId) {
            return false;
        }
        if (this.reactionId != other.reactionId) {
            return false;
        }
        if (this.userId != other.userId) {
            return false;
        }
        return true;
    }

    @Override
    public String toString() {
        return "gov.anl.aps.logr.portal.model.db.entities.LogReactionPK[ logId=" + logId + ", reactionId=" + reactionId + ", userId=" + userId + " ]";
    }
    
}
