/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.provider;

import gov.anl.aps.logr.rest.entities.DateParam;
import java.lang.annotation.Annotation;
import java.lang.reflect.Type;
import java.util.Date;
import javax.ws.rs.ext.ParamConverter;
import javax.ws.rs.ext.ParamConverterProvider;
import javax.ws.rs.ext.Provider;

/**
 * Registers a JAX-RS ParamConverter for java.util.Date query parameters.
 * Delegates parsing to DateParam, which supports ISO-8601,
 * "yyyy-MM-dd HH:mm:ss", and "yyyy-MM-dd" formats.
 *
 * @author djarosz
 */
@Provider
public class DateParamConverterProvider implements ParamConverterProvider {

    @Override
    @SuppressWarnings("unchecked")
    public <T> ParamConverter<T> getConverter(Class<T> rawType, Type genericType, Annotation[] annotations) {
        if (rawType != Date.class) {
            return null;
        }
        return (ParamConverter<T>) new ParamConverter<Date>() {
            @Override
            public Date fromString(String value) {
                if (value == null || value.isEmpty()) {
                    return null;
                }
                return new DateParam(value).getDate();
            }

            @Override
            public String toString(Date value) {
                if (value == null) {
                    return null;
                }
                return value.toString();
            }
        };
    }
}
