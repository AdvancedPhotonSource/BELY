/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.entities;

import com.fasterxml.jackson.annotation.JsonIgnore;
import java.io.Serializable;
import javax.persistence.EmbeddedId;
import javax.persistence.Entity;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;
import javax.persistence.NamedQueries;
import javax.persistence.NamedQuery;
import javax.persistence.Table;
import javax.xml.bind.annotation.XmlRootElement;

/**
 * Log Reaction entity class represents the log_reaction database table.
 *
 * @author djarosz
 */
@Entity
@Table(name = "log_reaction")
@XmlRootElement
@NamedQueries({
    @NamedQuery(name = "LogReaction.findAll", query = "SELECT l FROM LogReaction l"),
    @NamedQuery(name = "LogReaction.findByLogId", query = "SELECT l FROM LogReaction l WHERE l.logReactionPK.logId = :logId"),
    @NamedQuery(name = "LogReaction.findByReactionId", query = "SELECT l FROM LogReaction l WHERE l.logReactionPK.reactionId = :reactionId"),
    @NamedQuery(name = "LogReaction.findByUserId", query = "SELECT l FROM LogReaction l WHERE l.logReactionPK.userId = :userId")})
public class LogReaction implements Serializable {

    private static final long serialVersionUID = 1L;
    @EmbeddedId
    protected LogReactionPK logReactionPK;
    @JoinColumn(name = "log_id", referencedColumnName = "id", insertable = false, updatable = false)
    @ManyToOne(optional = false)
    private Log log;
    @JoinColumn(name = "reaction_id", referencedColumnName = "id", insertable = false, updatable = false)
    @ManyToOne(optional = false)
    private Reaction reaction;
    @JoinColumn(name = "user_id", referencedColumnName = "id", insertable = false, updatable = false)
    @ManyToOne(optional = false)
    private UserInfo userInfo;

    public LogReaction() {
    }

    public LogReaction(LogReactionPK logReactionPK) {
        this.logReactionPK = logReactionPK;
    }

    public LogReaction(int logId, int reactionId, int userId) {
        this.logReactionPK = new LogReactionPK(logId, reactionId, userId);
    }

    @JsonIgnore
    public LogReactionPK getLogReactionPK() {
        return logReactionPK;
    }

    public void setLogReactionPK(LogReactionPK logReactionPK) {
        this.logReactionPK = logReactionPK;
    }

    @JsonIgnore
    public Log getLog() {
        return log;
    }

    public void setLog(Log log) {
        this.log = log;
    }

    public Reaction getReaction() {
        return reaction;
    }

    public void setReaction(Reaction reaction) {
        this.reaction = reaction;
    }

    public UserInfo getUserInfo() {
        return userInfo;
    }

    public void setUserInfo(UserInfo userInfo) {
        this.userInfo = userInfo;
    }

    @Override
    public int hashCode() {
        int hash = 0;
        hash += (logReactionPK != null ? logReactionPK.hashCode() : 0);
        return hash;
    }

    @Override
    public boolean equals(Object object) {
        // TODO: Warning - this method won't work in the case the id fields are not set
        if (!(object instanceof LogReaction)) {
            return false;
        }
        LogReaction other = (LogReaction) object;
        if ((this.logReactionPK == null && other.logReactionPK != null) || (this.logReactionPK != null && !this.logReactionPK.equals(other.logReactionPK))) {
            return false;
        }
        return true;
    }

    @Override
    public String toString() {
        return "gov.anl.aps.logr.portal.model.db.entities.LogReaction[ logReactionPK=" + logReactionPK + " ]";
    }

}
