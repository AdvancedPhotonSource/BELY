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
import javax.validation.constraints.Size;
import javax.xml.bind.annotation.XmlRootElement;

/**
 *
 * @author djarosz
 */
@Entity
@Table(name = "notification_configuration_setting")
@XmlRootElement
@NamedQueries({
    @NamedQuery(name = "NotificationConfigurationSetting.findAll", query = "SELECT n FROM NotificationConfigurationSetting n"),
    @NamedQuery(name = "NotificationConfigurationSetting.findById", query = "SELECT n FROM NotificationConfigurationSetting n WHERE n.id = :id"),
    @NamedQuery(name = "NotificationConfigurationSetting.findByConfigValue", query = "SELECT n FROM NotificationConfigurationSetting n WHERE n.configValue = :configValue")})
public class NotificationConfigurationSetting implements Serializable {

    private static final long serialVersionUID = 1L;
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Basic(optional = false)
    @Column(name = "id")
    private Integer id;
    @Size(max = 256)
    @Column(name = "config_value")
    private String configValue;
    @JoinColumn(name = "notification_configuration_id", referencedColumnName = "id")
    @ManyToOne(optional = false)
    private NotificationConfiguration notificationConfiguration;
    @JoinColumn(name = "notification_provider_config_key_id", referencedColumnName = "id")
    @ManyToOne(optional = false)
    private NotificationProviderConfigKey notificationProviderConfigKey;

    public NotificationConfigurationSetting() {
    }

    public NotificationConfigurationSetting(Integer id) {
        this.id = id;
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

    public NotificationConfiguration getNotificationConfiguration() {
        return notificationConfiguration;
    }

    public void setNotificationConfiguration(NotificationConfiguration notificationConfiguration) {
        this.notificationConfiguration = notificationConfiguration;
    }

    public NotificationProviderConfigKey getNotificationProviderConfigKey() {
        return notificationProviderConfigKey;
    }

    public void setNotificationProviderConfigKey(NotificationProviderConfigKey notificationProviderConfigKey) {
        this.notificationProviderConfigKey = notificationProviderConfigKey;
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
        if (!(object instanceof NotificationConfigurationSetting)) {
            return false;
        }
        NotificationConfigurationSetting other = (NotificationConfigurationSetting) object;
        if ((this.id == null && other.id != null) || (this.id != null && !this.id.equals(other.id))) {
            return false;
        }
        return true;
    }

    @Override
    public String toString() {
        return "gov.anl.aps.logr.portal.model.db.entities.NotificationConfigurationSetting[ id=" + id + " ]";
    }

}
