/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.entities;

import java.io.Serializable;
import java.util.Collection;
import javax.persistence.Basic;
import javax.persistence.CascadeType;
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;
import javax.persistence.NamedQueries;
import javax.persistence.NamedQuery;
import javax.persistence.OneToMany;
import javax.persistence.Table;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Size;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.XmlTransient;

/**
 *
 * @author djarosz
 */
@Entity
@Table(name = "notification_provider_config_key")
@XmlRootElement
@NamedQueries({
    @NamedQuery(name = "NotificationProviderConfigKey.findAll", query = "SELECT n FROM NotificationProviderConfigKey n"),
    @NamedQuery(name = "NotificationProviderConfigKey.findById", query = "SELECT n FROM NotificationProviderConfigKey n WHERE n.id = :id"),
    @NamedQuery(name = "NotificationProviderConfigKey.findByConfigKey", query = "SELECT n FROM NotificationProviderConfigKey n WHERE n.configKey = :configKey"),
    @NamedQuery(name = "NotificationProviderConfigKey.findByDescription", query = "SELECT n FROM NotificationProviderConfigKey n WHERE n.description = :description"),
    @NamedQuery(name = "NotificationProviderConfigKey.findByIsRequired", query = "SELECT n FROM NotificationProviderConfigKey n WHERE n.isRequired = :isRequired"),
    @NamedQuery(name = "NotificationProviderConfigKey.findByDisplayOrder", query = "SELECT n FROM NotificationProviderConfigKey n WHERE n.displayOrder = :displayOrder")})
public class NotificationProviderConfigKey implements Serializable {

    private static final long serialVersionUID = 1L;
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Basic(optional = false)
    @Column(name = "id")
    private Integer id;
    @Basic(optional = false)
    @NotNull
    @Size(min = 1, max = 64)
    @Column(name = "config_key")
    private String configKey;
    @Size(max = 256)
    @Column(name = "description")
    private String description;
    @Basic(optional = false)
    @NotNull
    @Column(name = "is_required")
    private Boolean isRequired;
    @Column(name = "display_order")
    private Integer displayOrder;
    @JoinColumn(name = "notification_provider_id", referencedColumnName = "id")
    @ManyToOne(optional = false)
    private NotificationProvider notificationProviderId;
    @OneToMany(cascade = CascadeType.ALL, mappedBy = "notificationProviderConfigKeyId")
    private Collection<NotificationConfigurationSetting> notificationConfigurationSettingCollection;

    public NotificationProviderConfigKey() {
    }

    public NotificationProviderConfigKey(Integer id) {
        this.id = id;
    }

    public NotificationProviderConfigKey(Integer id, String configKey, Boolean isRequired) {
        this.id = id;
        this.configKey = configKey;
        this.isRequired = isRequired;
    }

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public String getConfigKey() {
        return configKey;
    }

    public void setConfigKey(String configKey) {
        this.configKey = configKey;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public Boolean getIsRequired() {
        return isRequired;
    }

    public void setIsRequired(Boolean isRequired) {
        this.isRequired = isRequired;
    }

    public Integer getDisplayOrder() {
        return displayOrder;
    }

    public void setDisplayOrder(Integer displayOrder) {
        this.displayOrder = displayOrder;
    }

    public NotificationProvider getNotificationProviderId() {
        return notificationProviderId;
    }

    public void setNotificationProviderId(NotificationProvider notificationProviderId) {
        this.notificationProviderId = notificationProviderId;
    }

    @XmlTransient
    public Collection<NotificationConfigurationSetting> getNotificationConfigurationSettingCollection() {
        return notificationConfigurationSettingCollection;
    }

    public void setNotificationConfigurationSettingCollection(Collection<NotificationConfigurationSetting> notificationConfigurationSettingCollection) {
        this.notificationConfigurationSettingCollection = notificationConfigurationSettingCollection;
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
        if (!(object instanceof NotificationProviderConfigKey)) {
            return false;
        }
        NotificationProviderConfigKey other = (NotificationProviderConfigKey) object;
        if ((this.id == null && other.id != null) || (this.id != null && !this.id.equals(other.id))) {
            return false;
        }
        return true;
    }

    @Override
    public String toString() {
        return "gov.anl.aps.logr.portal.model.db.entities.NotificationProviderConfigKey[ id=" + id + " ]";
    }
    
}
