/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.entities;

import com.fasterxml.jackson.annotation.JsonIgnore;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
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
@Table(name = "notification_configuration")
@XmlRootElement
@NamedQueries({
    @NamedQuery(name = "NotificationConfiguration.findAll", query = "SELECT n FROM NotificationConfiguration n"),
    @NamedQuery(name = "NotificationConfiguration.findById", query = "SELECT n FROM NotificationConfiguration n WHERE n.id = :id"),
    @NamedQuery(name = "NotificationConfiguration.findByName", query = "SELECT n FROM NotificationConfiguration n WHERE n.name = :name"),
    @NamedQuery(name = "NotificationConfiguration.findByDescription", query = "SELECT n FROM NotificationConfiguration n WHERE n.description = :description"),
    @NamedQuery(name = "NotificationConfiguration.findByNotificationEndpoint", query = "SELECT n FROM NotificationConfiguration n WHERE n.notificationEndpoint = :notificationEndpoint")})
public class NotificationConfiguration extends CdbEntity implements Serializable {

    private static final long serialVersionUID = 1L;
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Basic(optional = false)
    @Column(name = "id")
    private Integer id;
    @Basic(optional = false)
    @NotNull
    @Size(min = 1, max = 64)
    @Column(name = "name")
    private String name;
    @Size(max = 256)
    @Column(name = "description")
    private String description;
    @Basic(optional = false)
    @NotNull
    @Size(min = 1, max = 256)
    @Column(name = "notification_endpoint")
    private String notificationEndpoint;
    @JoinColumn(name = "notification_provider_id", referencedColumnName = "id")
    @ManyToOne(optional = false)
    private NotificationProvider notificationProvider;
    @JoinColumn(name = "user_id", referencedColumnName = "id")
    @ManyToOne(optional = true)
    private UserInfo userInfo;
    @OneToMany(cascade = CascadeType.ALL, mappedBy = "notificationConfiguration")
    private Collection<NotificationConfigurationHandlerSetting> notificationConfigurationHandlerSettingCollection;
    @OneToMany(cascade = CascadeType.ALL, mappedBy = "notificationConfiguration")
    private Collection<NotificationConfigurationSetting> notificationConfigurationSettingCollection;

    // Variables for create/update notificaiton configuration  
    private transient List<NotificationProviderConfigKey> providerConfigKeys = new ArrayList<>();
    private transient Map<Integer, String> configSettings = new HashMap<>();  // config key ID -> value
    private transient Map<Integer, Boolean> handlerPreferences = new HashMap<>();    // handler key ID -> enabled

    public NotificationConfiguration() {
    }

    public NotificationConfiguration(Integer id) {
        this.id = id;
    }

    public NotificationConfiguration(Integer id, String name, String notificationEndpoint) {
        this.id = id;
        this.name = name;
        this.notificationEndpoint = notificationEndpoint;
    }

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getNotificationEndpoint() {
        return notificationEndpoint;
    }

    public void setNotificationEndpoint(String notificationEndpoint) {
        this.notificationEndpoint = notificationEndpoint;
    }

    public String getNotificationProviderName() {
        return notificationProvider.getName();
    }

    @JsonIgnore
    public NotificationProvider getNotificationProvider() {
        return notificationProvider;
    }

    public void setNotificationProvider(NotificationProvider notificationProvider) {
        this.notificationProvider = notificationProvider;
    }

    public String getUsername() {
        if (userInfo == null) {
            return null;
        }

        return userInfo.getUsername();

    }

    @JsonIgnore
    public UserInfo getUserInfo() {
        return userInfo;
    }

    public void setUserInfo(UserInfo userInfo) {
        this.userInfo = userInfo;
    }

    @XmlTransient
    public Collection<NotificationConfigurationHandlerSetting> getNotificationConfigurationHandlerSettingCollection() {
        return notificationConfigurationHandlerSettingCollection;
    }

    public void setNotificationConfigurationHandlerSettingCollection(Collection<NotificationConfigurationHandlerSetting> notificationConfigurationHandlerSettingCollection) {
        this.notificationConfigurationHandlerSettingCollection = notificationConfigurationHandlerSettingCollection;
    }

    @XmlTransient
    public Collection<NotificationConfigurationSetting> getNotificationConfigurationSettingCollection() {
        return notificationConfigurationSettingCollection;
    }

    public void setNotificationConfigurationSettingCollection(Collection<NotificationConfigurationSetting> notificationConfigurationSettingCollection) {
        this.notificationConfigurationSettingCollection = notificationConfigurationSettingCollection;
    }

    public boolean isNewEntity() {
        return getId() == null;
    }

    @JsonIgnore
    public List<NotificationProviderConfigKey> getProviderConfigKeys() {
        return providerConfigKeys;
    }

    public void setProviderConfigKeys(List<NotificationProviderConfigKey> providerConfigKeys) {
        this.providerConfigKeys = providerConfigKeys;
    }

    @JsonIgnore
    public Map<Integer, String> getConfigSettings() {
        return configSettings;
    }

    public void setConfigSettings(Map<Integer, String> configSettings) {
        this.configSettings = configSettings;
    }

    @JsonIgnore
    public Map<Integer, Boolean> getHandlerPreferences() {
        return handlerPreferences;
    }

    public void setHandlerPreferences(Map<Integer, Boolean> handlerPreferences) {
        this.handlerPreferences = handlerPreferences;
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
        if (!(object instanceof NotificationConfiguration)) {
            return false;
        }
        NotificationConfiguration other = (NotificationConfiguration) object;
        if ((this.id == null && other.id != null) || (this.id != null && !this.id.equals(other.id))) {
            return false;
        }
        return true;
    }

    @Override
    public String toString() {
        return "gov.anl.aps.logr.portal.model.db.entities.NotificationConfiguration[ id=" + id + " ]";
    }

}
