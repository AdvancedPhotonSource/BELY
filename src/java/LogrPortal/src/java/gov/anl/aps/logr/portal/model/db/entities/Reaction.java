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
 * Reaction entity class represents the reaction database table. 
 * 
 * @author djarosz
 */
@Entity
@Table(name = "reaction")
@XmlRootElement
@NamedQueries({
    @NamedQuery(name = "Reaction.findAll", query = "SELECT r FROM Reaction r"),
    @NamedQuery(name = "Reaction.findAllSorted", query = "SELECT r FROM Reaction r ORDER BY r.sortOrder ASC"),
    @NamedQuery(name = "Reaction.findById", query = "SELECT r FROM Reaction r WHERE r.id = :id"),
    @NamedQuery(name = "Reaction.findByName", query = "SELECT r FROM Reaction r WHERE r.name = :name"),
    @NamedQuery(name = "Reaction.findByEmojiCode", query = "SELECT r FROM Reaction r WHERE r.emojiCode = :emojiCode"),
    @NamedQuery(name = "Reaction.findByDescription", query = "SELECT r FROM Reaction r WHERE r.description = :description")})
public class Reaction implements Serializable {

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
    @Basic(optional = false)
    @NotNull
    @Column(name = "emoji_code")
    private int emojiCode;
    @Size(max = 256)
    @Column(name = "description")
    private String description;
    @Column(name = "sort_order")
    private Float sortOrder;    
    @OneToMany(cascade = CascadeType.ALL, mappedBy = "reaction")
    private Collection<LogReaction> logReactionCollection;
    
    
    private transient String emoji; 

    public Reaction() {
    }

    public Reaction(Integer id) {
        this.id = id;
    }

    public Reaction(Integer id, String name, int emojiCode) {
        this.id = id;
        this.name = name;
        this.emojiCode = emojiCode;
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

    public int getEmojiCode() {
        return emojiCode;
    }

    public void setEmojiCode(int emojiCode) {
        this.emojiCode = emojiCode;
    }

    public String getEmoji() {
        if (emoji == null) {
            char[] charPair = Character.toChars(emojiCode); 
            emoji = new String(charPair); 
        }
        return emoji;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    @XmlTransient
    public Collection<LogReaction> getLogReactionCollection() {
        return logReactionCollection;
    }

    public void setLogReactionCollection(Collection<LogReaction> logReactionCollection) {
        this.logReactionCollection = logReactionCollection;
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
        if (!(object instanceof Reaction)) {
            return false;
        }
        Reaction other = (Reaction) object;
        if ((this.id == null && other.id != null) || (this.id != null && !this.id.equals(other.id))) {
            return false;
        }
        return true;
    }

    @Override
    public String toString() {
        return "gov.anl.aps.logr.portal.model.db.entities.Reaction[ id=" + id + " ]";
    }
    
}
