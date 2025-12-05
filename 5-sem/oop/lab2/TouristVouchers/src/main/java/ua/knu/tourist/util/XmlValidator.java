package ua.knu.tourist.util;

import javax.xml.XMLConstants;
import javax.xml.transform.stream.StreamSource;
import javax.xml.validation.Schema;
import javax.xml.validation.SchemaFactory;
import javax.xml.validation.Validator;
import java.io.File;
import java.io.IOException;

public class XmlValidator {

    //метод повертає true, якщо XML валідний
    public static boolean validate(File xsdFile, File xmlFile) {
        try {
            //W3C XML Schema
            SchemaFactory factory = SchemaFactory.newInstance(XMLConstants.W3C_XML_SCHEMA_NS_URI);

            //завантажуємо XSD
            Schema schema = factory.newSchema(xsdFile);

            //створюємо валідатор
            Validator validator = schema.newValidator();

            //перевіряємо XML
            validator.validate(new StreamSource(xmlFile));

            return true; //якщо помилок немає, доходимо сюди
        } catch (Exception e) {
            System.err.println("Validation Error: " + e.getMessage());
            return false;
        }
    }
}