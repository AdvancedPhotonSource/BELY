/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.entities;

import gov.anl.aps.logr.common.utilities.FileUtility;
import gov.anl.aps.logr.portal.utilities.GalleryUtility;
import gov.anl.aps.logr.portal.utilities.StorageUtility;
import java.io.Serializable;
import java.util.List;
import javax.persistence.Basic;
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.ManyToMany;
import javax.persistence.NamedQueries;
import javax.persistence.NamedQuery;
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
@Table(name="attachment")
@XmlRootElement
@NamedQueries({
    @NamedQuery(name = "Attachment.findAll", query = "SELECT a FROM Attachment a"),
    @NamedQuery(name = "Attachment.findById", query = "SELECT a FROM Attachment a WHERE a.id = :id"),
    @NamedQuery(name = "Attachment.findByName", query = "SELECT a FROM Attachment a WHERE a.name = :name"),
    @NamedQuery(name = "Attachment.findByTag", query = "SELECT a FROM Attachment a WHERE a.tag = :tag"),
    @NamedQuery(name = "Attachment.findByDescription", query = "SELECT a FROM Attachment a WHERE a.description = :description")})
public class Attachment implements Serializable {

    private static final long serialVersionUID = 1L;
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Basic(optional = false)
    private Integer id;
    @Basic(optional = false)
    @NotNull
    @Size(min = 1, max = 128)
    private String name;
   @Size(min = 1, max = 256)
   @Column(name = "original_filename")
   private String originalFilename;
    @Size(max = 64)
    private String tag;
    @Size(max = 256)
    private String description;
    @ManyToMany(mappedBy = "attachmentList")
    private List<Log> logList;
    
    private transient String filePath = null;
    private transient String galleryFilePath = null;

    public Attachment() {
    }

    public Attachment(Integer id) {
        this.id = id;
    }

    public Attachment(Integer id, String name) {
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

   public String getOriginalFilename() {
       return originalFilename;
   }

   public void setOriginalFilename(String originalFilename) {
       this.originalFilename = FileUtility.shortenFileNameIfNeeded(originalFilename, name, 256);        
   }
    
    public String getDisplayName() {
        if (tag != null && !tag.isEmpty()) {
            return tag;
        }
        return name; 
    }

    public String getTag() {
        return tag;
    }

    public void setTag(String tag) {
        this.tag = tag;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    @XmlTransient
    public List<Log> getLogList() {
        return logList;
    }

    public void setLogList(List<Log> logList) {
        this.logList = logList;
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
        if (!(object instanceof Attachment)) {
            return false;
        }
        Attachment other = (Attachment) object;
        if ((this.id == null && other.id != null) || (this.id != null && !this.id.equals(other.id))) {
            return false;
        }
        return true;
    }

    @Override
    public String toString() {
        return "gov.anl.aps.cdb.portal.model.db.entities.Attachment[ id=" + id + " ]";
    }
    
     public String getFilePath() {
        if (filePath == null) {
            filePath = StorageUtility.getApplicationLogAttachmentPath(name);
        }
        return filePath;
    }
     
    public String getLogAttachmentPath() {
        return StorageUtility.getLogAttachmentPath(name);
    }
     
    public String getGalleryFilePath() {
       if (galleryFilePath == null) {
           if (GalleryUtility.viewableFileName(name)) {
                galleryFilePath = getLogAttachmentPath();
           } else {
                galleryFilePath="/resources/images/file.svg";     
           }
           
       }
        return galleryFilePath;
    }
     
     
    
}
