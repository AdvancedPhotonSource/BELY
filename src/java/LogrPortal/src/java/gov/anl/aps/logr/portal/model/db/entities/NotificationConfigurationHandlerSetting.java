/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.entities;

import java.io.Serializable;
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
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Size;
import javax.xml.bind.annotation.XmlRootElement;

/**
 *
 * @author djarosz
 */
@Entity
@Table(name = "notification_configuration_handler_setting")
@XmlRootElement
@NamedQueries({
    @NamedQuery(name = "NotificationConfigurationHandlerSetting.findAll", query = "SELECT n FROM NotificationConfigurationHandlerSetting n"),
    @NamedQuery(name = "NotificationConfigurationHandlerSetting.findById", query = "SELECT n FROM NotificationConfigurationHandlerSetting n WHERE n.id = :id"),
    @NamedQuery(name = "NotificationConfigurationHandlerSetting.findByConfigValue", query = "SELECT n FROM NotificationConfigurationHandlerSetting n WHERE n.configValue = :configValue")})
public class NotificationConfigurationHandlerSetting implements Serializable {

    private static final long serialVersionUID = 1L;
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Basic(optional = false)
    @Column(name = "id")
    private Integer id;
    @Basic(optional = false)
    @NotNull
    @Size(min = 1, max = 256)
    @Column(name = "config_value")
    private String configValue;
    @JoinColumn(name = "notification_configuration_id", referencedColumnName = "id")
    @ManyToOne(optional = false)
    private NotificationConfiguration notificationConfigurationId;
    @JoinColumn(name = "notification_handler_config_key_id", referencedColumnName = "id")
    @ManyToOne(optional = false)
    private NotificationHandlerConfigKey notificationHandlerConfigKeyId;

    public NotificationConfigurationHandlerSetting() {
    }

    public NotificationConfigurationHandlerSetting(Integer id) {
        this.id = id;
    }

    public NotificationConfigurationHandlerSetting(Integer id, String configValue) {
        this.id = id;
        this.configValue = configValue;
    }

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public String getConfigValue() {
        return configValue;
    }

    public void setConfigValue(String configValue) {
        this.configValue = configValue;
    }

    public NotificationConfiguration getNotificationConfigurationId() {
        return notificationConfigurationId;
    }

    public void setNotificationConfigurationId(NotificationConfiguration notificationConfigurationId) {
        this.notificationConfigurationId = notificationConfigurationId;
    }

    public NotificationHandlerConfigKey getNotificationHandlerConfigKeyId() {
        return notificationHandlerConfigKeyId;
    }

    public void setNotificationHandlerConfigKeyId(NotificationHandlerConfigKey notificationHandlerConfigKeyId) {
        this.notificationHandlerConfigKeyId = notificationHandlerConfigKeyId;
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
        if (!(object instanceof NotificationConfigurationHandlerSetting)) {
            return false;
        }
        NotificationConfigurationHandlerSetting other = (NotificationConfigurationHandlerSetting) object;
        if ((this.id == null && other.id != null) || (this.id != null && !this.id.equals(other.id))) {
            return false;
        }
        return true;
    }

    @Override
    public String toString() {
        return "gov.anl.aps.logr.portal.model.db.entities.NotificationConfigurationHandlerSetting[ id=" + id + " ]";
    }
    
}
