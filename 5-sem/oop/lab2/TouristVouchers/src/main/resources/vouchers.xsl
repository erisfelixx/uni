<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:v="http://www.example.com/touristVouchers">

    <xsl:output method="html" encoding="UTF-8" indent="yes"/>

    <xsl:template match="/">
        <html>
            <head>
                <meta charset="UTF-8"/>
                <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
                <title>Туристичні путівки - Каталог</title>
                <style>
                    * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                    }

                    body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 40px 20px;
                    }

                    .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    }

                    h1 {
                    text-align: center;
                    color: white;
                    font-size: 2.5em;
                    margin-bottom: 15px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                    }

                    .subtitle {
                    text-align: center;
                    color: rgba(255,255,255,0.9);
                    font-size: 1.1em;
                    margin-bottom: 40px;
                    }

                    .vouchers-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                    gap: 30px;
                    margin-top: 30px;
                    }

                    .voucher-card {
                    background: white;
                    border-radius: 20px;
                    overflow: hidden;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                    position: relative;
                    }

                    .voucher-card:hover {
                    transform: translateY(-10px);
                    box-shadow: 0 15px 40px rgba(0,0,0,0.3);
                    }

                    .card-header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 25px;
                    position: relative;
                    }

                    .voucher-type {
                    display: inline-block;
                    background: rgba(255,255,255,0.2);
                    padding: 6px 15px;
                    border-radius: 20px;
                    font-size: 0.85em;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    margin-bottom: 10px;
                    }

                    .country-name {
                    font-size: 1.8em;
                    font-weight: bold;
                    margin: 10px 0;
                    }

                    .voucher-id {
                    position: absolute;
                    top: 15px;
                    right: 20px;
                    background: rgba(0,0,0,0.2);
                    padding: 5px 12px;
                    border-radius: 15px;
                    font-size: 0.8em;
                    font-family: monospace;
                    }

                    .card-body {
                    padding: 25px;
                    }

                    .info-row {
                    display: flex;
                    align-items: center;
                    margin-bottom: 15px;
                    padding: 12px;
                    background: #f8f9fa;
                    border-radius: 10px;
                    transition: background 0.2s;
                    }

                    .info-row:hover {
                    background: #e9ecef;
                    }

                    .info-icon {
                    width: 40px;
                    height: 40px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-right: 15px;
                    font-size: 1.2em;
                    flex-shrink: 0;
                    }

                    .info-label {
                    font-weight: 600;
                    color: #495057;
                    min-width: 90px;
                    }

                    .info-value {
                    color: #212529;
                    flex: 1;
                    }

                    .hotel-section {
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    padding: 20px;
                    border-radius: 15px;
                    margin: 20px 0;
                    color: white;
                    }

                    .hotel-title {
                    font-size: 1.2em;
                    font-weight: bold;
                    margin-bottom: 15px;
                    display: flex;
                    align-items: center;
                    }

                    .stars {
                    color: #ffd700;
                    font-size: 1.3em;
                    letter-spacing: 3px;
                    margin-bottom: 10px;
                    }

                    .hotel-features {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 10px;
                    margin-top: 15px;
                    }

                    .feature-item {
                    background: rgba(255,255,255,0.2);
                    padding: 8px 12px;
                    border-radius: 8px;
                    font-size: 0.9em;
                    display: flex;
                    align-items: center;
                    }

                    .feature-item::before {
                    content: '✓';
                    margin-right: 8px;
                    font-weight: bold;
                    }

                    .price-section {
                    background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
                    padding: 20px;
                    border-radius: 15px;
                    text-align: center;
                    margin-top: 20px;
                    }

                    .price-label {
                    font-size: 0.9em;
                    color: #333;
                    font-weight: 600;
                    margin-bottom: 5px;
                    }

                    .price-amount {
                    font-size: 2.2em;
                    font-weight: bold;
                    color: #fff;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
                    }

                    @media (max-width: 768px) {
                    .vouchers-grid {
                    grid-template-columns: 1fr;
                    }

                    h1 {
                    font-size: 2em;
                    }

                    .country-name {
                    font-size: 1.5em;
                    }
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Туристичні путівки</h1>
                    <div class="vouchers-grid">
                        <xsl:apply-templates select="v:TouristVouchers/v:TouristVoucher"/>
                    </div>
                </div>
            </body>
        </html>
    </xsl:template>

    <xsl:template match="v:TouristVoucher">
        <div class="voucher-card">
            <div class="card-header">
                <div class="voucher-id">
                    <xsl:value-of select="@id"/>
                </div>
                <div class="voucher-type">
                    <xsl:value-of select="v:Type"/>
                </div>
                <div class="country-name">
                    <xsl:value-of select="v:Country"/>
                </div>
            </div>

            <div class="card-body">
                <div class="info-row">
                    <div class="info-icon">📅</div>
                    <span class="info-label">Тривалість:</span>
                    <span class="info-value">
                        <xsl:value-of select="v:DaysNights/v:Days"/> днів /
                        <xsl:value-of select="v:DaysNights/v:Nights"/> ночей
                    </span>
                </div>

                <div class="info-row">
                    <div class="info-icon">🚗</div>
                    <span class="info-label">Транспорт:</span>
                    <span class="info-value">
                        <xsl:value-of select="v:Transport"/>
                    </span>
                </div>

                <div class="hotel-section">
                    <div class="hotel-title">Готель</div>
                    <div class="stars">
                        <xsl:call-template name="print-stars">
                            <xsl:with-param name="count" select="v:Hotel/v:Stars"/>
                        </xsl:call-template>
                    </div>

                    <div class="hotel-features">
                        <div class="feature-item">
                            Харчування: <xsl:value-of select="v:Hotel/v:Food"/>
                        </div>
                        <div class="feature-item">
                            Місць: <xsl:value-of select="v:Hotel/v:RoomPlaces"/>
                        </div>
                        <xsl:if test="v:Hotel/v:TV = 'true'">
                            <div class="feature-item">📺 Телевізор</div>
                        </xsl:if>
                        <xsl:if test="v:Hotel/v:AirConditioning = 'true'">
                            <div class="feature-item">❄️ Кондиціонер</div>
                        </xsl:if>
                    </div>
                </div>

                <div class="price-section">
                    <div class="price-label">Вартість</div>
                    <div class="price-amount">
                        <xsl:value-of select="v:Cost"/>
                        <xsl:text> </xsl:text>
                        <xsl:value-of select="v:Cost/@currency"/>
                    </div>
                </div>
            </div>
        </div>
    </xsl:template>

    <xsl:template name="print-stars">
        <xsl:param name="count"/>
        <xsl:if test="$count > 0">
            ★
            <xsl:call-template name="print-stars">
                <xsl:with-param name="count" select="$count - 1"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>

</xsl:stylesheet>