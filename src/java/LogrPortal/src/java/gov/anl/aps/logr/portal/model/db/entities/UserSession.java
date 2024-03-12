/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.entities;

import java.io.Serializable;
import java.util.Date;
import javax.persistence.Basic;
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;
import javax.persistence.NamedQueries;
import javax.persistence.NamedQuery;
import javax.persistence.Table;
import javax.persistence.Temporal;
import javax.persistence.TemporalType;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Size;
import javax.xml.bind.annotation.XmlRootElement;

/**
 * User Session entity class represents the user_session database table. 
 *
 * @author djarosz
 */
@Entity
@Table(name = "user_session")
@XmlRootElement
@NamedQueries({
    @NamedQuery(name = "UserSession.findAll", query = "SELECT u FROM UserSession u"),
    @NamedQuery(name = "UserSession.findById", query = "SELECT u FROM UserSession u WHERE u.id = :id"),
    @NamedQuery(name = "UserSession.findBySessionName", query = "SELECT u FROM UserSession u WHERE u.sessionName = :sessionName"),
    @NamedQuery(name = "UserSession.findByExpirationDateTime", query = "SELECT u FROM UserSession u WHERE u.expirationDateTime = :expirationDateTime"),
    @NamedQuery(name = "UserSession.findBySessionKey", query = "SELECT u FROM UserSession u WHERE u.sessionKey = :sessionKey and u.expirationDateTime > CURRENT_TIMESTAMP")})
public class UserSession implements Serializable {

    private static final long serialVersionUID = 1L;
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Basic(optional = false)
    @Column(name = "id")
    private Integer id;
    @Size(max = 128)
    @Column(name = "session_name")
    private String sessionName;
    @Basic(optional = false)
    @NotNull
    @Column(name = "expiration_date_time")
    @Temporal(TemporalType.TIMESTAMP)
    private Date expirationDateTime;
    @Basic(optional = false)
    @NotNull
    @Size(min = 1, max = 256)
    @Column(name = "session_key")
    private String sessionKey;
    @JoinColumn(name = "user_id", referencedColumnName = "id")
    @ManyToOne(optional = false)
    private UserInfo userInfo;

    public UserSession() {
    }

    public UserSession(Integer id) {
        this.id = id;
    }

    public UserSession(Integer id, Date expirationDateTime, String sessionKey) {
        this.id = id;
        this.expirationDateTime = expirationDateTime;
        this.sessionKey = sessionKey;
    }

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public String getSessionName() {
        return sessionName;
    }

    public void setSessionName(String sessionName) {
        this.sessionName = sessionName;
    }

    public Date getExpirationDateTime() {
        return expirationDateTime;
    }

    public void setExpirationDateTime(Date expirationDateTime) {
        this.expirationDateTime = expirationDateTime;
    }

    public String getSessionKey() {
        return sessionKey;
    }

    public void setSessionKey(String sessionKey) {
        this.sessionKey = sessionKey;
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
        hash += (id != null ? id.hashCode() : 0);
        return hash;
    }

    @Override
    public boolean equals(Object object) {
        // TODO: Warning - this method won't work in the case the id fields are not set
        if (!(object instanceof UserSession)) {
            return false;
        }
        UserSession other = (UserSession) object;
        if ((this.id == null && other.id != null) || (this.id != null && !this.id.equals(other.id))) {
            return false;
        }
        return true;
    }

    @Override
    public String toString() {
        return "gov.anl.aps.logr.portal.model.db.entities.UserSession[ id=" + id + " ]";
    }
    
}
