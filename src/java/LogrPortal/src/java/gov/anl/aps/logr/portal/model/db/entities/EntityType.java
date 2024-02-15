/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.entities;

import com.fasterxml.jackson.annotation.JsonIgnore;
import java.io.Serializable;
import java.util.List;
import javax.persistence.Basic;
import javax.persistence.Cacheable;
import javax.persistence.CascadeType;
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.JoinColumn;
import javax.persistence.JoinTable;
import javax.persistence.ManyToMany;
import javax.persistence.ManyToOne;
import javax.persistence.NamedQueries;
import javax.persistence.NamedQuery;
import javax.persistence.OneToMany;
import javax.persistence.OrderBy;
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
@Cacheable(true)
@Table(name = "entity_type")
@XmlRootElement
@NamedQueries({
    @NamedQuery(name = "EntityType.findAll", query = "SELECT e FROM EntityType e"),
    @NamedQuery(name = "EntityType.findById", query = "SELECT e FROM EntityType e WHERE e.id = :id"),
    @NamedQuery(name = "EntityType.findByName", query = "SELECT e FROM EntityType e WHERE e.name = :name"),
    @NamedQuery(name = "EntityType.findByDescription", query = "SELECT e FROM EntityType e WHERE e.description = :description"),    
    @NamedQuery(name = "EntityType.findTopLevelByDomain", query = "SELECT e FROM EntityType e INNER JOIN e.allowedDomainList adl WHERE adl.id = :allowedDomainId AND e.isInternal = FALSE AND e.parentEntityType is NULL ORDER BY e.sortOrder ASC"),
})
public class EntityType extends CdbEntity implements Serializable {

    private static final long serialVersionUID = 1L;
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Basic(optional = false)
    private Integer id;
    @Basic(optional = false)
    @NotNull
    @Size(min = 1, max = 64)
    private String name;
    @Column(name = "display_name")
    @NotNull
    @Size(min = 1, max = 128)    
    private String displayName;
    @Column(name = "long_display_name")    
    @Size(max = 256)
    private String longDisplayName;    
    @Size(max = 256)
    private String description;
    @Column(name = "custom_list_url")
    @Size(max = 64)
    private String customListUrl;
    @JoinColumn(name = "parent_entity_type_id", referencedColumnName = "id")
    @ManyToOne
    private EntityType parentEntityType;
    @Column(name = "sort_order")
    private Float sortOrder;    
    @Column(name = "is_internal")
    @NotNull
    private boolean isInternal;   
    @OneToMany(mappedBy = "parentEntityType")
    @OrderBy("sortOrder ASC")
    private List<EntityType> entityTypeChildren;    
    @JoinTable(name = "allowed_entity_type_domain", joinColumns = {
        @JoinColumn(name = "entity_type_id", referencedColumnName = "id")}, inverseJoinColumns = {
        @JoinColumn(name = "domain_id", referencedColumnName = "id")})
    @ManyToMany        
    private List<Domain> allowedDomainList;        
    @JoinTable(name = "allowed_child_entity_type", joinColumns = {
        @JoinColumn(name = "parent_entity_type_id", referencedColumnName = "id")}, inverseJoinColumns = {
        @JoinColumn(name = "child_entity_type_id", referencedColumnName = "id")})
    @ManyToMany        
    private List<EntityType> allowedEntityTypeList;
    @ManyToMany(mappedBy = "allowedEntityTypeList")
    private List<EntityType> entityTypeList1;
    @ManyToMany(mappedBy = "entityTypeList")
    private List<Item> itemList;
    @ManyToMany(mappedBy = "entityTypeList")
    private List<PropertyType> propertyTypeList;
    @JoinColumn(name = "primary_template_item_id", referencedColumnName = "id")
    @ManyToOne(cascade = CascadeType.ALL)
    private Item primaryTemplateItem;
    
    private transient String listUrl = null; 

    public EntityType() {
    }

    public EntityType(Integer id) {
        this.id = id;
    }

    public EntityType(Integer id, String name) {
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
        // Do not allow spaces.         
        name = name.replace(" ", "-"); 
        
        this.name = name;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    @XmlTransient
    public List<EntityType> getAllowedEntityTypeList() {
        return allowedEntityTypeList;
    }

    public void setAllowedEntityTypeList(List<EntityType> allowedEntityTypeList) {
        this.allowedEntityTypeList = allowedEntityTypeList;
    }

    @XmlTransient
    public List<EntityType> getEntityTypeList1() {
        return entityTypeList1;
    }

    public void setEntityTypeList1(List<EntityType> entityTypeList1) {
        this.entityTypeList1 = entityTypeList1;
    }

    @XmlTransient
    public List<Item> getItemList() {
        return itemList;
    }

    public void setItemList(List<Item> itemList) {
        this.itemList = itemList;
    }

    @XmlTransient
    public List<PropertyType> getPropertyTypeList() {
        return propertyTypeList;
    }

    public void setPropertyTypeList(List<PropertyType> propertyTypeList) {
        this.propertyTypeList = propertyTypeList;
    }

    @XmlTransient
    public String getDisplayName() {
        return displayName;
    }

    public void setDisplayName(String displayName) { 
        this.displayName = displayName;
    }

    @XmlTransient
    public String getLongDisplayName() {
        return longDisplayName;
    }

    public void setLongDisplayName(String longDisplayName) {
        this.longDisplayName = longDisplayName;
    }

    @XmlTransient
    public String getCustomListUrl() {
        return customListUrl;
    }

    public void setCustomListUrl(String customListUrl) {
        if (customListUrl.isBlank()) {
            customListUrl = null; 
        }
        this.customListUrl = customListUrl;
    }

    @XmlTransient
    public EntityType getParentEntityType() {
        return parentEntityType;
    }

    public void setParentEntityType(EntityType parentEntityType) {
        this.parentEntityType = parentEntityType;
    }

    @XmlTransient
    public Float getSortOrder() {
        return sortOrder;
    }

    public void setSortOrder(Float sortOrder) {
        this.sortOrder = sortOrder;
    }

    @XmlTransient
    public Boolean getIsInternal() {
        return isInternal;
    }

    public void setIsInternal(Boolean isInternal) {
        this.isInternal = isInternal;
    }

    @XmlTransient
    public List<EntityType> getEntityTypeChildren() {
        return entityTypeChildren;
    }

    public void setEntityTypeChildren(List<EntityType> entityTypeChildren) {
        this.entityTypeChildren = entityTypeChildren;
    }

    @XmlTransient
    public List<Domain> getAllowedDomainList() {
        return allowedDomainList;
    }

    public void setAllowedDomainList(List<Domain> allowedDomainList) {
        this.allowedDomainList = allowedDomainList;
    }

    @XmlTransient
    public Item getPrimaryTemplateItem() {
        return primaryTemplateItem;
    }

    public void setPrimaryTemplateItem(Item primaryTemplateItem) {
        this.primaryTemplateItem = primaryTemplateItem;
    }    
    
    @JsonIgnore
    public boolean isHasChildren() {
        return !entityTypeChildren.isEmpty(); 
    }
    
    @JsonIgnore    
    public String getListUrl() {
        if (listUrl == null) {
            if (customListUrl != null) {
                listUrl = customListUrl; 
            } else {
                listUrl = String.format("list?et=%d", id); 
            }
        }
        return listUrl;
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
        if (!(object instanceof EntityType)) {
            return false;
        }
        EntityType other = (EntityType) object;
        if ((this.id == null && other.id != null) || (this.id != null && !this.id.equals(other.id))) {
            return false;
        }
        return true;
    }

    @Override
    public String toString() {
        return getName();
    }
    
}
