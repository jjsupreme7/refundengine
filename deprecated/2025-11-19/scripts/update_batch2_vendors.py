#!/usr/bin/env python3
"""
Update Supabase with Batch 2 researched vendor data (vendors 16-40)
"""

from core.database import get_supabase_client
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Batch 2: Researched vendor data (vendors 16-40)
BATCH2_VENDORS = [{"vendor_name": "INVUE SECURITY PRODUCTS INC",
                   "industry": "Retail Security Solutions",
                   "business_model": "B2B Manufacturing & IoT",
                   "typical_delivery": "Physical security products + cloud software",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Retail security solutions - merchandise protection, access control, POS peripherals",  # noqa: E501
                   "primary_products": [{"name": "Asset Protection Products",
                                         "type": "tangible_personal_property",
                                         "description": "Smart locks, display stands, locked cabinets, alarming devices",  # noqa: E501
                                         },
                                        {"name": "Access Control",
                                         "type": "tangible_personal_property",
                                         "description": "Access control solutions for retail",  # noqa: E501
                                         },
                                        {"name": "OneKEY Ecosystem",
                                         "type": "saas_subscription",
                                         "description": "IoT platform for tracking merchandise interactions",  # noqa: E501
                                         },
                                        {"name": "POS Peripherals",
                                         "type": "tangible_personal_property",
                                         "description": "Point of sale security peripherals",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 2007. Acquired by ASSA ABLOY. Uses LoRaWAN for IoT. Serves major retailers globally.",  # noqa: E501
                   },
                  {"vendor_name": "TRIAD MANUFACTURING INC",
                   "industry": "Retail Fixtures Manufacturing",
                   "business_model": "B2B Manufacturing",
                   "typical_delivery": "Manufacturing + installation services",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Custom retail fixtures and displays - wood, metal, design, installation",  # noqa: E501
                   "primary_products": [{"name": "Custom Fixtures",
                                         "type": "tangible_personal_property",
                                         "description": "Wood and metal retail fixtures",  # noqa: E501
                                         },
                                        {"name": "Display Systems",
                                         "type": "tangible_personal_property",
                                         "description": "Custom retail displays with LED, interactive tech",  # noqa: E501
                                         },
                                        {"name": "Installation Services",
                                         "type": "construction_services",
                                         "description": "Store planning, installation, site surveys",  # noqa: E501
                                         },
                                        {"name": "Design Engineering",
                                         "type": "professional_services",
                                         "description": "Fixture design and prototyping",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Saint Louis, MO. 32 years in business. 1.8M+ sq ft US facilities, 4M+ sq ft offshore. Serves flagship to pop-up stores.",  # noqa: E501
                   },
                  {"vendor_name": "NATIONAL MAINTENANCE & CONSTRUCTION",
                   "industry": "Facilities & Construction Services",
                   "business_model": "B2B Services",
                   "typical_delivery": "On-site construction and maintenance",
                   "wa_tax_classification": "construction_services",
                   "product_description": "National facilities and construction management - new construction, remodeling, maintenance",  # noqa: E501
                   "primary_products": [{"name": "Construction Services",
                                         "type": "construction_services",
                                         "description": "New construction, remodeling, mixed-use properties",  # noqa: E501
                                         },
                                        {"name": "Facilities Maintenance",
                                         "type": "professional_services",
                                         "description": "Commercial, industrial, retail property maintenance",  # noqa: E501
                                         },
                                        {"name": "Project Management",
                                         "type": "professional_services",
                                         "description": "Nationwide construction project management",  # noqa: E501
                                         },
                                        {"name": "Janitorial Services",
                                         "type": "professional_services",
                                         "description": "Commercial janitorial and specialty services",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Multiple entities found: NMC (Federal Way WA), NM&C Inc (Boca Raton FL). 50+ years combined experience. 50K+ vendor network.",  # noqa: E501
                   },
                  {"vendor_name": "ELOQUENT CORP",
                   "industry": "Telecommunications Equipment",
                   "business_model": "B2B Distribution",
                   "typical_delivery": "Physical product shipment",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Telecommunications equipment - headsets, audio/video conferencing, unified communications",  # noqa: E501
                   "primary_products": [{"name": "Headsets",
                                         "type": "tangible_personal_property",
                                         "description": "Wireless and corded telecommunications headsets",  # noqa: E501
                                         },
                                        {"name": "Conferencing Equipment",
                                         "type": "tangible_personal_property",
                                         "description": "Audio and video conferencing systems",  # noqa: E501
                                         },
                                        {"name": "Unified Communications",
                                         "type": "tangible_personal_property",
                                         "description": "UC audio devices and peripherals",  # noqa: E501
                                         },
                                        {"name": "Telecom Consulting",
                                         "type": "professional_services",
                                         "description": "Telecommunications consulting services",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Carnation, WA. 1-10 employees. Professional, Scientific, and Technical Services industry.",  # noqa: E501
                   },
                  {"vendor_name": "ACCURATE BACKGROUND LLC",
                   "industry": "Employment Screening Services",
                   "business_model": "B2B SaaS + Services",
                   "typical_delivery": "Cloud-based screening platform",
                   "wa_tax_classification": "professional_services",
                   "product_description": "Employment background screening and workforce monitoring - criminal checks, drug testing, verifications",  # noqa: E501
                   "primary_products": [{"name": "Background Screening",
                                         "type": "professional_services",
                                         "description": "Criminal, civil, credit checks, employment verification",  # noqa: E501
                                         },
                                        {"name": "Drug Testing",
                                         "type": "professional_services",
                                         "description": "Drug and health screening services",  # noqa: E501
                                         },
                                        {"name": "Screening Platform",
                                         "type": "saas_subscription",
                                         "description": "Cloud platform with ATS integrations",  # noqa: E501
                                         },
                                        {"name": "I-9 & E-Verify",
                                         "type": "professional_services",
                                         "description": "Form I-9 and employment eligibility verification",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Largest privately held, minority-owned background screening provider. 24/7 support. Clients: Amazon, Starbucks, Sephora.",  # noqa: E501
                   },
                  {"vendor_name": "BROADRIDGE MAIL LLC",
                   "industry": "Financial Printing & Mailing",
                   "business_model": "B2B Services",
                   "typical_delivery": "Printing and mailing services",
                   "wa_tax_classification": "professional_services",
                   "product_description": "Financial printing and direct mail - investor communications, postal optimization",  # noqa: E501
                   "primary_products": [{"name": "Print & Delivery",
                                         "type": "professional_services",
                                         "description": "Financial document printing, 3.5B packages/year",  # noqa: E501
                                         },
                                        {"name": "Direct Mail Marketing",
                                         "type": "professional_services",
                                         "description": "FINRA-reviewed direct mail for financial services",  # noqa: E501
                                         },
                                        {"name": "Postal Optimization",
                                         "type": "professional_services",
                                         "description": "Smart commingling, address hygiene, presort",  # noqa: E501
                                         },
                                        {"name": "Digital Communications",
                                         "type": "saas_subscription",
                                         "description": "Multi-channel customer communications platform",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Global Fintech leader. $6B+ revenue. SSAE18 certified. Specializes in financial services industry communications.",  # noqa: E501
                   },
                  {"vendor_name": "POWERHOUSE RETAIL SERVICES LLC",
                   "industry": "Retail Facilities Services",
                   "business_model": "B2B Services",
                   "typical_delivery": "Nationwide on-site services",
                   "wa_tax_classification": "construction_services",
                   "product_description": "Multi-site retail facilities maintenance and construction - rollouts, installations, maintenance",  # noqa: E501
                   "primary_products": [{"name": "Fixture Installation",
                                         "type": "construction_services",
                                         "description": "National rollouts, graphics, fixture installations",  # noqa: E501
                                         },
                                        {"name": "Store Construction",
                                         "type": "construction_services",
                                         "description": "Remodels, refreshes, store-in-store projects",  # noqa: E501
                                         },
                                        {"name": "Facilities Maintenance",
                                         "type": "professional_services",
                                         "description": "Scheduled and reactive maintenance services",  # noqa: E501
                                         },
                                        {"name": "Exterior Services",
                                         "type": "professional_services",
                                         "description": "Landscaping, snow removal, lot sweeping",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Crowley, TX. 600 employees. Serves all 50 states. 24/7/365 support. Blue-chip multi-site brands. Acquired by Lincolnshire Management.",  # noqa: E501
                   },
                  {"vendor_name": "ARCHITECTURAL GRAPHICS INC",
                   "industry": "Signage Manufacturing & Services",
                   "business_model": "B2B Services",
                   "typical_delivery": "Manufacturing + nationwide installation",
                   "wa_tax_classification": "construction_services",
                   "product_description": "Architectural interior and exterior signage - design, manufacturing, installation, maintenance",  # noqa: E501
                   "primary_products": [{"name": "Sign Systems",
                                         "type": "tangible_personal_property",
                                         "description": "Architectural interior and exterior sign systems",  # noqa: E501
                                         },
                                        {"name": "Multi-Location Signage",
                                         "type": "construction_services",
                                         "description": "National multi-location sign programs",  # noqa: E501
                                         },
                                        {"name": "Installation Services",
                                         "type": "construction_services",
                                         "description": "Nationwide installation and permitting",  # noqa: E501
                                         },
                                        {"name": "Maintenance Services",
                                         "type": "professional_services",
                                         "description": "Ongoing sign maintenance and image services",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 1969. Virginia Beach, VA. Serves GM, Ford, SunTrust, Key Bank, PNC, Firestone, FedEx Office. 18% YoY growth since 2007.",  # noqa: E501
                   },
                  {"vendor_name": "PRINCIPLE USA INC",
                   "industry": "Business Consulting & Analytics",
                   "business_model": "B2B Consulting Services",
                   "typical_delivery": "Professional services + cloud analytics",
                   "wa_tax_classification": "professional_services",
                   "product_description": "Business consulting and data analytics - Salesforce, Google Marketing Platform, predictive analytics",  # noqa: E501
                   "primary_products": [{"name": "Data Analytics Consulting",
                                         "type": "professional_services",
                                         "description": "Predictive analytics, decision support solutions",  # noqa: E501
                                         },
                                        {"name": "Salesforce Implementation",
                                         "type": "professional_services",
                                         "description": "Salesforce technology consulting and implementation",  # noqa: E501
                                         },
                                        {"name": "Marketing Analytics",
                                         "type": "professional_services",
                                         "description": "Google Marketing Platform partnership, SEO, paid marketing",  # noqa: E501
                                         },
                                        {"name": "Data Visualization",
                                         "type": "saas_subscription",
                                         "description": "Real-time charting and analytics dashboards",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Knoxville, TN. 80+ employees. Google Marketing Platform Partner. 51-200 employees per Dun & Bradstreet.",  # noqa: E501
                   },
                  {"vendor_name": "PROSYS INFORMATION SYSTEMS",
                   "industry": "IT Managed Services",
                   "business_model": "B2B IT Services",
                   "typical_delivery": "Managed services + cloud solutions",
                   "wa_tax_classification": "professional_services",
                   "product_description": "IT managed services and solutions - cybersecurity, cloud, networking, data center",  # noqa: E501
                   "primary_products": [{"name": "Managed IT Services",
                                         "type": "professional_services",
                                         "description": "Infrastructure management, support, operations",  # noqa: E501
                                         },
                                        {"name": "Cybersecurity Solutions",
                                         "type": "saas_subscription",
                                         "description": "Enterprise security, threat management",  # noqa: E501
                                         },
                                        {"name": "Cloud Services",
                                         "type": "iaas_paas",
                                         "description": "Cloud migration, infrastructure, virtualization",  # noqa: E501
                                         },
                                        {"name": "Network Solutions",
                                         "type": "professional_services",
                                         "description": "Cisco networking, wireless, contact center",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Norcross, GA. Women's Business Enterprise (WBE). National/Gold Cisco Partner. Partnership with Computacenter for global scale.",  # noqa: E501
                   },
                  {"vendor_name": "QUALITY BUSINESS SYSTEMS",
                   "industry": "Office Equipment Services",
                   "business_model": "B2B Sales & Services",
                   "typical_delivery": "Equipment sales/lease + service",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Office equipment - copiers, printers, multifunction devices, managed print services",  # noqa: E501
                   "primary_products": [{"name": "Copiers & Printers",
                                         "type": "tangible_personal_property",
                                         "description": "Commercial copiers, printers, MFDs",  # noqa: E501
                                         },
                                        {"name": "Managed Print Services",
                                         "type": "professional_services",
                                         "description": "Print management, monitoring, supply fulfillment",  # noqa: E501
                                         },
                                        {"name": "Document Management",
                                         "type": "saas_subscription",
                                         "description": "Document workflow and management solutions",  # noqa: E501
                                         },
                                        {"name": "Service & Maintenance",
                                         "type": "professional_services",
                                         "description": "24/7 technical support and repair",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Multiple Quality-branded companies found. Kyocera authorized dealers. Typical services: sales, leasing, maintenance, supplies.",  # noqa: E501
                   },
                  {"vendor_name": "TAILWIND VOICE & DATA INC",
                   "industry": "Telecommunications Services",
                   "business_model": "B2B Telecom Services",
                   "typical_delivery": "Network services + on-site installation",
                   "wa_tax_classification": "telecommunications",
                   "product_description": "Enterprise telecommunications and network services - voice, data, cabling, managed connectivity",  # noqa: E501
                   "primary_products": [{"name": "Voice & Data Services",
                                         "type": "telecommunications",
                                         "description": "Voice and data communications, unified billing",  # noqa: E501
                                         },
                                        {"name": "Network Solutions",
                                         "type": "professional_services",
                                         "description": "Network management, structured cabling, configuration",  # noqa: E501
                                         },
                                        {"name": "Cloud Services",
                                         "type": "iaas_paas",
                                         "description": "Cloud connectivity and infrastructure",  # noqa: E501
                                         },
                                        {"name": "Service Management",
                                         "type": "professional_services",
                                         "description": "Asset management, connectivity management, always-on support",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 2005. Minnetonka, MN. 80 employees, $16.4M revenue. Serves multi-location enterprises. Healthcare, hospitality, retail focus.",  # noqa: E501
                   },
                  {"vendor_name": "CASS INFORMATION SYSTEMS INC",
                   "industry": "Payment & Invoice Processing",
                   "business_model": "B2B Financial Services",
                   "typical_delivery": "Cloud-based processing platform",
                   "wa_tax_classification": "professional_services",
                   "product_description": "Payment and information processing - freight audit, utility bill management, invoice processing",  # noqa: E501
                   "primary_products": [{"name": "Freight Invoice Management",
                                         "type": "professional_services",
                                         "description": "Transportation invoice rating, audit, payment",  # noqa: E501
                                         },
                                        {"name": "Utility Bill Management",
                                         "type": "professional_services",
                                         "description": "Energy invoice processing, electricity, gas, waste",  # noqa: E501
                                         },
                                        {"name": "Invoice Processing Platform",
                                         "type": "saas_subscription",
                                         "description": "AI/ML invoice processing, 245K invoices daily",  # noqa: E501
                                         },
                                        {"name": "Banking Services",
                                         "type": "financial_services",
                                         "description": "Commercial banking via Cass Commercial Bank",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Manages $90B+ in payables annually. SSAE18 certified. AI/ML/OCR technology. Publicly traded (CASS). Banking subsidiary.",  # noqa: E501
                   },
                  {"vendor_name": "ANIXTER INC",
                   "industry": "Electrical & Network Distribution",
                   "business_model": "B2B Distribution",
                   "typical_delivery": "Product distribution + technical services",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Distributor of communications, security, electrical, network products and wire/cable",  # noqa: E501
                   "primary_products": [{"name": "Network & Security Products",
                                         "type": "tangible_personal_property",
                                         "description": "Communications and security equipment",  # noqa: E501
                                         },
                                        {"name": "Electrical Products",
                                         "type": "tangible_personal_property",
                                         "description": "Electrical and electronic wire and cable",  # noqa: E501
                                         },
                                        {"name": "Utility Power Solutions",
                                         "type": "tangible_personal_property",
                                         "description": "Utility power distribution products",  # noqa: E501
                                         },
                                        {"name": "Technical Services",
                                         "type": "professional_services",
                                         "description": "Application engineering and technical support",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 1957. Acquired by WESCO International 2020 for $4.5B. Now operates as Wesco Anixter. Glenview, IL.",  # noqa: E501
                   },
                  {"vendor_name": "PRIORITY INC",
                   "industry": "Payment Technology",
                   "business_model": "B2B Payment Solutions",
                   "typical_delivery": "Cloud payment platforms",
                   "wa_tax_classification": "professional_services",
                   "product_description": "Payment technology and processing - merchant services, B2B payments, embedded finance",  # noqa: E501
                   "primary_products": [{"name": "SMB Payment Solutions",
                                         "type": "saas_subscription",
                                         "description": "MX Connect and MX Merchant platforms",  # noqa: E501
                                         },
                                        {"name": "B2B Payment Platform",
                                         "type": "saas_subscription",
                                         "description": "CPX platform: AP automation, virtual card, ACH+",  # noqa: E501
                                         },
                                        {"name": "Enterprise Payments",
                                         "type": "professional_services",
                                         "description": "Payment processing for large enterprises",  # noqa: E501
                                         },
                                        {"name": "Embedded Finance",
                                         "type": "saas_subscription",
                                         "description": "BaaS solutions for platform modernization",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Priority Technology Holdings (PRTH). Founded 2005. Alpharetta, GA. Public company. Three segments: SMB, B2B, Enterprise.",  # noqa: E501
                   },
                  {"vendor_name": "ERICSSON INC",
                   "industry": "Telecommunications Equipment",
                   "business_model": "B2B Manufacturing",
                   "typical_delivery": "Network equipment + professional services",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Telecommunications network equipment - 5G, 4G, radio access, IP transport, software",  # noqa: E501
                   "primary_products": [{"name": "5G Network Equipment",
                                         "type": "tangible_personal_property",
                                         "description": "5G RAN, AirScale radios, massive MIMO, basebands",  # noqa: E501
                                         },
                                        {"name": "Network Software",
                                         "type": "software_license",
                                         "description": "5G Core, cloud-native network functions",  # noqa: E501
                                         },
                                        {"name": "IP & Optical Transport",
                                         "type": "tangible_personal_property",
                                         "description": "Transport systems and routers",
                                         },
                                        {"name": "Professional Services",
                                         "type": "professional_services",
                                         "description": "Network deployment, optimization, engineering",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Swedish multinational. Stockholm headquarters. 160+ 5G networks globally. US 5G manufacturer. Carries 60% of US wireless traffic.",  # noqa: E501
                   },
                  {"vendor_name": "VISUAL OPTIONS INC",
                   "industry": "Retail Displays & Merchandising",
                   "business_model": "B2B Manufacturing",
                   "typical_delivery": "Product manufacturing + installation",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Retail display fixtures and visual merchandising (tentative - limited data)",  # noqa: E501
                   "primary_products": [{"name": "Display Fixtures",
                                         "type": "tangible_personal_property",
                                         "description": "Retail display fixtures and merchandising",  # noqa: E501
                                         },
                                        {"name": "Visual Merchandising",
                                         "type": "professional_services",
                                         "description": "Store displays and visual merchandising services",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "TENTATIVE DATA - specific company not confirmed in search results. Industry inferred from name. Needs additional verification.",  # noqa: E501
                   },
                  {"vendor_name": "GENERAL DATATECH",
                   "industry": "IT Solutions & Integration",
                   "business_model": "B2B IT Services",
                   "typical_delivery": "Professional services + cloud solutions",
                   "wa_tax_classification": "professional_services",
                   "product_description": "IT solutions provider and systems integrator - networking, security, cloud, data center",  # noqa: E501
                   "primary_products": [{"name": "Network Solutions",
                                         "type": "professional_services",
                                         "description": "Enterprise networking, SD-WAN, collaboration",  # noqa: E501
                                         },
                                        {"name": "Security Services",
                                         "type": "professional_services",
                                         "description": "Advanced security, threat management",  # noqa: E501
                                         },
                                        {"name": "Cloud Services",
                                         "type": "iaas_paas",
                                         "description": "Cloud advisory, migration, hybrid-cloud deployment",  # noqa: E501
                                         },
                                        {"name": "SmartX Edge",
                                         "type": "professional_services",
                                         "description": "IoT, physical security, asset tracking, AI",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "GDT. Founded 1996. Dallas, TX. $1.4B revenue. 450+ certifications. Partners: Cisco, HPE, NetApp, Juniper. Bangalore tech center.",  # noqa: E501
                   },
                  {"vendor_name": "TEMPEST TELECOM SOLUTIONS LLC",
                   "industry": "Telecommunications Equipment & Services",
                   "business_model": "B2B Services",
                   "typical_delivery": "Equipment supply + technical services",
                   "wa_tax_classification": "telecommunications",
                   "product_description": "Network solutions provider - equipment supply, repair, logistics, technical services",  # noqa: E501
                   "primary_products": [{"name": "Telecom Equipment",
                                         "type": "tangible_personal_property",
                                         "description": "Multi-vendor network equipment supply",  # noqa: E501
                                         },
                                        {"name": "Equipment Repair",
                                         "type": "professional_services",
                                         "description": "Network equipment repair and refurbishment",  # noqa: E501
                                         },
                                        {"name": "Logistics Services",
                                         "type": "professional_services",
                                         "description": "Asset management, equipment disposition",  # noqa: E501
                                         },
                                        {"name": "Technical Services",
                                         "type": "professional_services",
                                         "description": "Network deployment, testing, remote technical support",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Santa Barbara, CA. Women Business Enterprise (WBE). Serves telecom carriers, network operators. All network generations supported.",  # noqa: E501
                   },
                  {"vendor_name": "LANE VALENTE INDUSTRIES INC",
                   "industry": "Facility Services & Construction",
                   "business_model": "B2B Services",
                   "typical_delivery": "On-site services nationwide",
                   "wa_tax_classification": "construction_services",
                   "product_description": "Multi-site facility maintenance and construction - electrical, HVAC, EV charging, project management",  # noqa: E501
                   "primary_products": [{"name": "Facility Maintenance",
                                         "type": "professional_services",
                                         "description": "Electrical, HVAC, lighting, maintenance services",  # noqa: E501
                                         },
                                        {"name": "EV Charging Infrastructure",
                                         "type": "construction_services",
                                         "description": "EV charging station installation, 6,200+ sites",  # noqa: E501
                                         },
                                        {"name": "Construction Services",
                                         "type": "construction_services",
                                         "description": "Remodels, fixture installations, new construction",  # noqa: E501
                                         },
                                        {"name": "Energy Solutions",
                                         "type": "professional_services",
                                         "description": "Energy reduction, lighting upgrades, value engineering",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Smithtown, NY. 12+ years EV charging experience. Serves US, Puerto Rico, Canada. Multi-site organizations. 38% cost savings claimed.",  # noqa: E501
                   },
                  {"vendor_name": "STAPLES CONTRACT AND COMMERCIAL INC",
                   "industry": "Office Supplies B2B",
                   "business_model": "B2B Distribution",
                   "typical_delivery": "Product distribution",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Business-to-business office supplies, technology, furniture, facilities supplies, breakroom",  # noqa: E501
                   "primary_products": [{"name": "Office Supplies",
                                         "type": "tangible_personal_property",
                                         "description": "Paper, ink, toner, organizational products",  # noqa: E501
                                         },
                                        {"name": "Technology Products",
                                         "type": "tangible_personal_property",
                                         "description": "Computers, printers, electronics",  # noqa: E501
                                         },
                                        {"name": "Furniture",
                                         "type": "tangible_personal_property",
                                         "description": "Office furniture and fixtures",
                                         },
                                        {"name": "Facilities Supplies",
                                         "type": "tangible_personal_property",
                                         "description": "Janitorial, breakroom, facilities products",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Staples Business Advantage division. Framingham, MA / Overland Park, KS. GSA contracts. Serves businesses, institutions, government.",  # noqa: E501
                   },
                  {"vendor_name": "BUSINESS INTERIORS NORTHWEST INC",
                   "industry": "Office Furniture & Design",
                   "business_model": "B2B Services",
                   "typical_delivery": "Furniture sales + design services",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Office furniture dealer - furniture sales, workspace design, installation",  # noqa: E501
                   "primary_products": [{"name": "Office Furniture",
                                         "type": "tangible_personal_property",
                                         "description": "Herman Miller and other commercial furniture",  # noqa: E501
                                         },
                                        {"name": "Workspace Design",
                                         "type": "professional_services",
                                         "description": "Office design and space planning",  # noqa: E501
                                         },
                                        {"name": "Installation Services",
                                         "type": "construction_services",
                                         "description": "Furniture installation and project management",  # noqa: E501
                                         },
                                        {"name": "Prefab Construction",
                                         "type": "construction_services",
                                         "description": "Prefab interior construction services",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 1982. Bellevue/Tukwila, WA. Herman Miller dealer. Now part of Catalyst Workplace Activation. Serves corporate, healthcare, education, government.",  # noqa: E501
                   },
                  {"vendor_name": "NOKIA SOLUTIONS AND NETWORKS US LLC",
                   "industry": "Telecommunications Equipment",
                   "business_model": "B2B Manufacturing",
                   "typical_delivery": "Network equipment + professional services",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "5G and telecommunications network equipment - radio access, core network, transport",  # noqa: E501
                   "primary_products": [{"name": "5G RAN Equipment",
                                         "type": "tangible_personal_property",
                                         "description": "AirScale radio units, massive MIMO, 5G base stations",  # noqa: E501
                                         },
                                        {"name": "Network Infrastructure",
                                         "type": "tangible_personal_property",
                                         "description": "Core network, IP routing, optical transport",  # noqa: E501
                                         },
                                        {"name": "Network Software",
                                         "type": "software_license",
                                         "description": "Cloud-native network software and management",  # noqa: E501
                                         },
                                        {"name": "Professional Services",
                                         "type": "professional_services",
                                         "description": "Network deployment, optimization, managed services",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Finnish multinational. Espoo, Finland HQ. Nokia subsidiary. 160+ 5G networks. Serves 29 of 30 largest service providers. US Federal Solutions unit.",  # noqa: E501
                   },
                  {"vendor_name": "BRINTON BUSINESS VENTURES INC",
                   "industry": "Vending & Refreshment Services",
                   "business_model": "B2B Services",
                   "typical_delivery": "Vending machines + service routes",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Refreshment services - vending, coffee services, catering, markets",  # noqa: E501
                   "primary_products": [{"name": "Vending Services",
                                         "type": "tangible_personal_property",
                                         "description": "Vending machines and product supply",  # noqa: E501
                                         },
                                        {"name": "Coffee Services",
                                         "type": "professional_services",
                                         "description": "Office coffee and breakroom services",  # noqa: E501
                                         },
                                        {"name": "Catering Services",
                                         "type": "professional_services",
                                         "description": "Corporate catering (Act 3 Catering brand)",  # noqa: E501
                                         },
                                        {"name": "Micro Markets",
                                         "type": "tangible_personal_property",
                                         "description": "Self-service micro market solutions",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Renton, WA. Brands: Evergreen Refreshments, Act 3 Catering, PGi Services, Peak Refreshments, Modern Plate, Avanti Markets NW.",  # noqa: E501
                   },
                  {"vendor_name": "SHAW INDUSTRIES INC",
                   "industry": "Flooring Manufacturing",
                   "business_model": "B2B/B2C Manufacturing",
                   "typical_delivery": "Product manufacturing + distribution",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Flooring manufacturer - carpet, hardwood, laminate, resilient, tile, synthetic tur",  # noqa: E501
                   "primary_products": [{"name": "Carpet",
                                         "type": "tangible_personal_property",
                                         "description": "Residential and commercial carpet",  # noqa: E501
                                         },
                                        {"name": "Hard Surface Flooring",
                                         "type": "tangible_personal_property",
                                         "description": "Hardwood, laminate, resilient, tile & stone",  # noqa: E501
                                         },
                                        {"name": "Synthetic Tur",
                                         "type": "tangible_personal_property",
                                         "description": "Commercial and sports synthetic turf",  # noqa: E501
                                         },
                                        {"name": "Commercial Flooring",
                                         "type": "tangible_personal_property",
                                         "description": "Commercial carpet tile, broadloom, LVT",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 1946 (Star Dye Company). Dalton, GA. $6B+ revenue. 22,000 employees. Berkshire Hathaway subsidiary (acquired 2001). World's largest carpet manufacturer.",  # noqa: E501
                   },
                  ]


def update_vendors():
    """Update Batch 2 vendors in Supabase"""

    print("Connecting to Supabase...")
    supabase = get_supabase_client()
    print("✓ Connected\n")

    print(f"Updating Batch 2: {len(BATCH2_VENDORS)} vendors (16-40)...\n")

    updated = 0
    errors = 0

    for vendor_data in BATCH2_VENDORS:
        vendor_name = vendor_data["vendor_name"]

        try:
            # Find vendor by name
            result = (
                supabase.table("vendor_products")
                .select("id")
                .eq("vendor_name", vendor_name)
                .execute()
            )

            if not result.data:
                print(f"❌ {vendor_name} - not found in database")
                errors += 1
                continue

            vendor_id = result.data[0]["id"]

            # Prepare update data
            update_data = {
                "industry": vendor_data["industry"],
                "business_model": vendor_data["business_model"],
                "typical_delivery": vendor_data["typical_delivery"],
                "wa_tax_classification": vendor_data["wa_tax_classification"],
                "product_description": vendor_data["product_description"],
                "primary_products": json.dumps(vendor_data["primary_products"]),
                "research_notes": vendor_data["research_notes"],
                "web_research_date": datetime.now().isoformat(),
            }

            # Update vendor
            supabase.table("vendor_products").update(update_data).eq(
                "id", vendor_id
            ).execute()

            print(f"✓ {vendor_name}")
            updated += 1

        except Exception as e:
            print(f"❌ {vendor_name} - Error: {e}")
            errors += 1

    print(f"\n{'=' * 70}")
    print("BATCH 2 UPDATE COMPLETE")
    print(f"{'=' * 70}")
    print(f"✓ Updated: {updated}")
    print(f"❌ Errors: {errors}")
    print(f"Total researched so far: {15 + updated} vendors")
    print(f"Remaining: {294 - 15 - updated} vendors")


if __name__ == "__main__":
    update_vendors()
