package ua.knu.tourist.util;

import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.stream.StreamResult;
import javax.xml.transform.stream.StreamSource;
import java.io.File;

public class XmlTransformer {

    public static void transformToHTML(File xmlFile, File xslFile, File htmlFile) {
        try {
            TransformerFactory factory = TransformerFactory.newInstance();

            // завантажуємо шаблон XSL
            Transformer transformer = factory.newTransformer(new StreamSource(xslFile));

            // XML + XSL = HTML
            transformer.transform(new StreamSource(xmlFile), new StreamResult(htmlFile));

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}