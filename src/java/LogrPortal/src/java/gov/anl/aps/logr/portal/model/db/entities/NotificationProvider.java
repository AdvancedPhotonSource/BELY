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
@Table(name = "notification_provider")
@XmlRootElement
@NamedQueries({
    @NamedQuery(name = "NotificationProvider.findAll", query = "SELECT n FROM NotificationProvider n"),
    @NamedQuery(name = "NotificationProvider.findById", query = "SELECT n FROM NotificationProvider n WHERE n.id = :id"),
    @NamedQuery(name = "NotificationProvider.findByName", query = "SELECT n FROM NotificationProvider n WHERE n.name = :name"),
    @NamedQuery(name = "NotificationProvider.findByDescription", query = "SELECT n FROM NotificationProvider n WHERE n.description = :description")})
public class NotificationProvider implements Serializable {

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
    @OneToMany(cascade = CascadeType.ALL, mappedBy = "notificationProvider")
    private Collection<NotificationProviderConfigKey> notificationProviderConfigKeyCollection;
    @OneToMany(cascade = CascadeType.ALL, mappedBy = "notificationProvider")
    private Collection<NotificationConfiguration> notificationConfigurationCollection;

    public NotificationProvider() {
    }

    public NotificationProvider(Integer id) {
        this.id = id;
    }

    public NotificationProvider(Integer id, String name) {
        this.id = id;
        this.name = name;
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

    @XmlTransient
    public Collection<NotificationProviderConfigKey> getNotificationProviderConfigKeyCollection() {
        return notificationProviderConfigKeyCollection;
    }

    public void setNotificationProviderConfigKeyCollection(Collection<NotificationProviderConfigKey> notificationProviderConfigKeyCollection) {
        this.notificationProviderConfigKeyCollection = notificationProviderConfigKeyCollection;
    }

    @XmlTransient
    public Collection<NotificationConfiguration> getNotificationConfigurationCollection() {
        return notificationConfigurationCollection;
    }

    public void setNotificationConfigurationCollection(Collection<NotificationConfiguration> notificationConfigurationCollection) {
        this.notificationConfigurationCollection = notificationConfigurationCollection;
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
        if (!(object instanceof NotificationProvider)) {
            return false;
        }
        NotificationProvider other = (NotificationProvider) object;
        if ((this.id == null && other.id != null) || (this.id != null && !this.id.equals(other.id))) {
            return false;
        }
        return true;
    }

    @Override
    public String toString() {
        return "gov.anl.aps.logr.portal.model.db.entities.NotificationProvider[ id=" + id + " ]";
    }

}
