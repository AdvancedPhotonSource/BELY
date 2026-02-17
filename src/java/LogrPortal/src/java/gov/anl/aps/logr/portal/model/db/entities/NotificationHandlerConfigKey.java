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
@Table(name = "notification_handler_config_key")
@XmlRootElement
@NamedQueries({
    @NamedQuery(name = "NotificationHandlerConfigKey.findAll", query = "SELECT n FROM NotificationHandlerConfigKey n"),
    @NamedQuery(name = "NotificationHandlerConfigKey.findById", query = "SELECT n FROM NotificationHandlerConfigKey n WHERE n.id = :id"),
    @NamedQuery(name = "NotificationHandlerConfigKey.findByConfigKey", query = "SELECT n FROM NotificationHandlerConfigKey n WHERE n.configKey = :configKey"),
    @NamedQuery(name = "NotificationHandlerConfigKey.findByDisplayName", query = "SELECT n FROM NotificationHandlerConfigKey n WHERE n.displayName = :displayName"),
    @NamedQuery(name = "NotificationHandlerConfigKey.findByDescription", query = "SELECT n FROM NotificationHandlerConfigKey n WHERE n.description = :description"),
    @NamedQuery(name = "NotificationHandlerConfigKey.findByValueType", query = "SELECT n FROM NotificationHandlerConfigKey n WHERE n.valueType = :valueType"),
    @NamedQuery(name = "NotificationHandlerConfigKey.findByDefaultValue", query = "SELECT n FROM NotificationHandlerConfigKey n WHERE n.defaultValue = :defaultValue"),
    @NamedQuery(name = "NotificationHandlerConfigKey.findByDisplayOrder", query = "SELECT n FROM NotificationHandlerConfigKey n WHERE n.displayOrder = :displayOrder")})
public class NotificationHandlerConfigKey implements Serializable {

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
    @Size(max = 64)
    @Column(name = "display_name")
    private String displayName;
    @Size(max = 256)
    @Column(name = "description")
    private String description;
    @Basic(optional = false)
    @NotNull
    @Size(min = 1, max = 7)
    @Column(name = "value_type")
    private String valueType;
    @Size(max = 256)
    @Column(name = "default_value")
    private String defaultValue;
    @Column(name = "display_order")
    private Integer displayOrder;
    @OneToMany(cascade = CascadeType.ALL, mappedBy = "notificationHandlerConfigKey")
    private Collection<NotificationConfigurationHandlerSetting> notificationConfigurationHandlerSettingCollection;

    public NotificationHandlerConfigKey() {
    }

    public NotificationHandlerConfigKey(Integer id) {
        this.id = id;
    }

    public NotificationHandlerConfigKey(Integer id, String configKey, String valueType) {
        this.id = id;
        this.configKey = configKey;
        this.valueType = valueType;
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

    public String getDisplayName() {
        return displayName;
    }

    public void setDisplayName(String displayName) {
        this.displayName = displayName;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getValueType() {
        return valueType;
    }

    public void setValueType(String valueType) {
        this.valueType = valueType;
    }

    public String getDefaultValue() {
        return defaultValue;
    }

    public void setDefaultValue(String defaultValue) {
        this.defaultValue = defaultValue;
    }

    public Integer getDisplayOrder() {
        return displayOrder;
    }

    public void setDisplayOrder(Integer displayOrder) {
        this.displayOrder = displayOrder;
    }

    @XmlTransient
    public Collection<NotificationConfigurationHandlerSetting> getNotificationConfigurationHandlerSettingCollection() {
        return notificationConfigurationHandlerSettingCollection;
    }

    public void setNotificationConfigurationHandlerSettingCollection(Collection<NotificationConfigurationHandlerSetting> notificationConfigurationHandlerSettingCollection) {
        this.notificationConfigurationHandlerSettingCollection = notificationConfigurationHandlerSettingCollection;
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
        if (!(object instanceof NotificationHandlerConfigKey)) {
            return false;
        }
        NotificationHandlerConfigKey other = (NotificationHandlerConfigKey) object;
        if ((this.id == null && other.id != null) || (this.id != null && !this.id.equals(other.id))) {
            return false;
        }
        return true;
    }

    @Override
    public String toString() {
        return "gov.anl.aps.logr.portal.model.db.entities.NotificationHandlerConfigKey[ id=" + id + " ]";
    }

}
