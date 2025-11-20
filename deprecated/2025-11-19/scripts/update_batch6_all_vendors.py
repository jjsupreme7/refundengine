#!/usr/bin/env python3
"""
Update Batch 6: All remaining vendors (141-294) - 154 vendors
Comprehensive research with headquarters locations and service areas
"""

from core.database import get_supabase_client
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Batch 6 Vendors: 141-294 (154 total)
BATCH6_VENDORS = [{"vendor_name": "ACCENT FOOD SERVICES LLC",
                   "industry": "Food Service & Vending",
                   "business_model": "B2B Food Services",
                   "typical_delivery": "Physical delivery + vending machines + mobile app",  # noqa: E501
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Breakroom and refreshment solutions - coffee, beverages, snacks, vending machines",  # noqa: E501
                   "primary_products": [{"name": "Vending Services",
                                         "type": "tangible_personal_property",
                                         "description": "Self-checkout vending machines with mobile app payments",  # noqa: E501
                                         },
                                        {"name": "Coffee & Beverages",
                                         "type": "tangible_personal_property",
                                         "description": "Coffee, tea, filtered water, healthy beverages",  # noqa: E501
                                         },
                                        {"name": "Food Service",
                                         "type": "tangible_personal_property",
                                         "description": "Snacks, entrees, salads, fresh-cut fruit",  # noqa: E501
                                         },
                                        {"name": "Breakroom Solutions",
                                         "type": "professional_services",
                                         "description": "Breakroom management and refreshment services",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 35+ years ago, acquired by Sodexo January 2022. Serves 10,000+ customers across 10 states with 700 employees.\n📍 HQ: Pflugerville, TX (2913 AW Grimes Blvd) | Service Area: TX, Western LA, Northwest NV, Lake Tahoe CA, Phoenix/Tucson AZ, MD, DC, Northern VA, WV, Southern PA (11 facilities total)",  # noqa: E501
                   },
                  {"vendor_name": "BUILD A SIGN LLC",
                   "industry": "Custom Printing & Signage",
                   "business_model": "B2B/B2C Online Printing",
                   "typical_delivery": "Physical shipment of printed materials",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Award-winning online custom printing provider - signage, apparel, home decor",  # noqa: E501
                   "primary_products": [{"name": "Custom Signage",
                                         "type": "tangible_personal_property",
                                         "description": "Banners, yard signs, vehicle wraps, window graphics",  # noqa: E501
                                         },
                                        {"name": "Printed Apparel",
                                         "type": "tangible_personal_property",
                                         "description": "Custom t-shirts, uniforms, promotional clothing",  # noqa: E501
                                         },
                                        {"name": "Home Decor",
                                         "type": "tangible_personal_property",
                                         "description": "Custom wall art, canvas prints, decorative items",  # noqa: E501
                                         },
                                        {"name": "Business Graphics",
                                         "type": "tangible_personal_property",
                                         "description": "Promotional materials, marketing collateral",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 2005. Acquired by Cimpress N.V. (PWP Growth Equity) September 2018 for $280M.\n📍 HQ: Austin, TX (11525 Stonehollow Dr Ste 100) | Service Area: National (online e-commerce platform)",  # noqa: E501
                   },
                  {"vendor_name": "TERADATA CORPORATIONS",
                   "industry": "Data Analytics & Cloud",
                   "business_model": "B2B Enterprise Software",
                   "typical_delivery": "Cloud platform + professional services",
                   "wa_tax_classification": "iaas_paas",
                   "product_description": "Enterprise data analytics solutions and trusted AI innovation platform",  # noqa: E501
                   "primary_products": [{"name": "Teradata Vantage",
                                         "type": "iaas_paas",
                                         "description": "Cloud data platform for analytics and AI/ML workloads",  # noqa: E501
                                         },
                                        {"name": "Data Warehouse",
                                         "type": "iaas_paas",
                                         "description": "Enterprise-scale data warehousing solutions",  # noqa: E501
                                         },
                                        {"name": "Analytics Services",
                                         "type": "professional_services",
                                         "description": "Data analytics consulting and implementation",  # noqa: E501
                                         },
                                        {"name": "AI Solutions",
                                         "type": "saas_subscription",
                                         "description": "Trusted AI innovation tools and platforms",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Major US locations: San Diego (HQ), Atlanta, San Francisco R&D. Global offices: London, Sydney, Tokyo.\n📍 HQ: San Diego, CA (17095 Via del Campo, 92127) | Service Area: Global",  # noqa: E501
                   },
                  {"vendor_name": "PORTIS & ASSOCIATES LLC",
                   "industry": "Construction & Millwork",
                   "business_model": "B2B Construction Services",
                   "typical_delivery": "On-site construction + manufactured fixtures",
                   "wa_tax_classification": "construction_services",
                   "product_description": "General contracting, construction management, specialty millwork and fixtures",  # noqa: E501
                   "primary_products": [{"name": "General Contracting",
                                         "type": "construction_services",
                                         "description": "Full-service general contracting nationwide",  # noqa: E501
                                         },
                                        {"name": "Construction Management",
                                         "type": "professional_services",
                                         "description": "Project planning and management services",  # noqa: E501
                                         },
                                        {"name": "Specialty Millwork",
                                         "type": "manufacturing",
                                         "description": "Custom millwork and fixture manufacturing",  # noqa: E501
                                         },
                                        {"name": "Fixture Installation",
                                         "type": "construction_services",
                                         "description": "Specialty product installation services",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 1980. Two divisions: construction (Orange, CA) and millwork (Salt Lake City, UT).\n📍 HQ: South Jordan, UT (1086 W South Jordan Pkwy Ste 101) | Service Area: Nationwide (construction office in Orange, CA; millwork in Salt Lake City, UT)",  # noqa: E501
                   },
                  {"vendor_name": "DOCUSIGN INC",
                   "industry": "Software - Digital Agreements",
                   "business_model": "B2B SaaS",
                   "typical_delivery": "Cloud-based platform",
                   "wa_tax_classification": "saas_subscription",
                   "product_description": "Electronic signature and digital agreement management platform",  # noqa: E501
                   "primary_products": [{"name": "eSignature",
                                         "type": "saas_subscription",
                                         "description": "Electronic signature solution for any device",  # noqa: E501
                                         },
                                        {"name": "Agreement Cloud",
                                         "type": "saas_subscription",
                                         "description": "Digital agreement lifecycle management",  # noqa: E501
                                         },
                                        {"name": "CLM",
                                         "type": "saas_subscription",
                                         "description": "Contract lifecycle management platform",  # noqa: E501
                                         },
                                        {"name": "Gen for Salesforce",
                                         "type": "saas_subscription",
                                         "description": "Document generation integrated with Salesforce",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 2003, HQ moved to San Francisco 2010. 1.7M clients in 180 countries. 6,838 employees total (850 in SF). Growing SF HQ to ~143,000 sq ft.\n📍 HQ: San Francisco, CA (221 Main Street, Suite 800) | Service Area: Global (180 countries)",  # noqa: E501
                   },
                  {"vendor_name": "SUNRISE CREATIVE GROUP INC",
                   "industry": "Marketing & Identity Services",
                   "business_model": "B2B Marketing Services",
                   "typical_delivery": "Professional services",
                   "wa_tax_classification": "professional_services",
                   "product_description": "Marketing and brand identity services (operates as Sunrise Identity)",  # noqa: E501
                   "primary_products": [{"name": "Brand Strategy",
                                         "type": "professional_services",
                                         "description": "Brand development and positioning services",  # noqa: E501
                                         },
                                        {"name": "Marketing Services",
                                         "type": "professional_services",
                                         "description": "Integrated marketing campaigns and services",  # noqa: E501
                                         },
                                        {"name": "Identity Design",
                                         "type": "professional_services",
                                         "description": "Brand identity and visual design",  # noqa: E501
                                         },
                                        {"name": "Creative Services",
                                         "type": "professional_services",
                                         "description": "Creative content and design services",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "DBA Sunrise Identity. Marketing and brand services provider.\n📍 HQ: Bellevue, WA (405 114th Ave SE, Ste 200, 98004) | Service Area: Pacific Northwest / National",  # noqa: E501
                   },
                  {"vendor_name": "ANRITSU COMPANY",
                   "industry": "Test & Measurement Equipment",
                   "business_model": "B2B Manufacturing",
                   "typical_delivery": "Physical equipment + software licenses",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Test and measurement equipment for telecom, networking, and quality assurance",  # noqa: E501
                   "primary_products": [{"name": "Network Testing Equipment",
                                         "type": "tangible_personal_property",
                                         "description": "5G/LTE testing, optical test equipment",  # noqa: E501
                                         },
                                        {"name": "Spectrum Analyzers",
                                         "type": "tangible_personal_property",
                                         "description": "RF and microwave spectrum analysis tools",  # noqa: E501
                                         },
                                        {"name": "QA Inspection Equipment",
                                         "type": "tangible_personal_property",
                                         "description": "Food and pharmaceutical quality assurance systems",  # noqa: E501
                                         },
                                        {"name": "Test Software",
                                         "type": "software_license",
                                         "description": "Measurement and analysis software platforms",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "North American subsidiary of Anritsu Corporation (Atsugi, Japan). Microwave Measurements Division in Morgan Hill, CA.\n📍 HQ: Morgan Hill, CA (490 Jarvis Drive, 95037) | Parent: Atsugi, Japan | Service Area: North America",  # noqa: E501
                   },
                  {"vendor_name": "INFOVISTA NETWORK TESTING INC",
                   "industry": "Telecom Network Solutions",
                   "business_model": "B2B Software & Services",
                   "typical_delivery": "Software platform + professional services",
                   "wa_tax_classification": "saas_subscription",
                   "product_description": "Network lifecycle automation - planning, testing, optimization for telecom",  # noqa: E501
                   "primary_products": [{"name": "Network Planning",
                                         "type": "saas_subscription",
                                         "description": "5G network planning and design automation",  # noqa: E501
                                         },
                                        {"name": "Network Testing",
                                         "type": "professional_services",
                                         "description": "Mobile and fixed network testing services",  # noqa: E501
                                         },
                                        {"name": "Network Assurance",
                                         "type": "saas_subscription",
                                         "description": "Performance monitoring and optimization",  # noqa: E501
                                         },
                                        {"name": "Network Automation",
                                         "type": "saas_subscription",
                                         "description": "Lifecycle automation for mobile/fixed/private networks",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Acquired Ascom Network Testing Division 2016. Specializes in telecommunications network automation.\n📍 HQ: Massy, France (3 Rue Christophe Colomb, 91300) | Americas Office: Lowell, MA (175 Cabot St Ste 460, 01854) | Service Area: Global",  # noqa: E501
                   },
                  {"vendor_name": "RENTACRATE ENTERPRISES LLC",
                   "industry": "Moving & Storage Supplies",
                   "business_model": "B2B/B2C Rental Services",
                   "typical_delivery": "Physical delivery and pickup of rental items",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Reusable moving crate rental services and moving supplies",  # noqa: E501
                   "primary_products": [{"name": "Crate Rental",
                                         "type": "tangible_personal_property",
                                         "description": "Reusable plastic moving crates for rent",  # noqa: E501
                                         },
                                        {"name": "Moving Supplies",
                                         "type": "tangible_personal_property",
                                         "description": "Boxes, packing materials, moving accessories",  # noqa: E501
                                         },
                                        {"name": "Delivery & Pickup",
                                         "type": "professional_services",
                                         "description": "Crate delivery and pickup services",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Eco-friendly moving crate rental company providing sustainable alternative to cardboard boxes.\n📍 HQ: Location TBD (regional operations) | Service Area: Regional/Metro areas",  # noqa: E501
                   },
                  {"vendor_name": "THYSSENKRUPP ELEVATOR CORP",
                   "industry": "Elevator & Escalator Services",
                   "business_model": "B2B Manufacturing & Services",
                   "typical_delivery": "Manufacturing + installation + maintenance services",  # noqa: E501
                   "wa_tax_classification": "construction_services",
                   "product_description": "Elevator, escalator, and moving walkway manufacturing, installation, and service (now TK Elevator)",  # noqa: E501
                   "primary_products": [{"name": "Elevator Systems",
                                         "type": "tangible_personal_property",
                                         "description": "Passenger and freight elevators",  # noqa: E501
                                         },
                                        {"name": "Escalators",
                                         "type": "tangible_personal_property",
                                         "description": "Commercial escalators and moving walkways",  # noqa: E501
                                         },
                                        {"name": "Installation Services",
                                         "type": "construction_services",
                                         "description": "Elevator/escalator installation and commissioning",  # noqa: E501
                                         },
                                        {"name": "Maintenance Services",
                                         "type": "professional_services",
                                         "description": "24/7 service, maintenance, and modernization",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Rebranded to TK Elevator 2020. One of world's largest elevator companies.\n📍 HQ: Atlanta, GA (North American headquarters) | Parent: Germany | Service Area: Global / Nationwide",  # noqa: E501
                   },
                  {"vendor_name": "CYBER-ARK SOFTWARE INC",
                   "industry": "Cybersecurity - Identity Security",
                   "business_model": "B2B Software",
                   "typical_delivery": "Cloud platform + software licenses",
                   "wa_tax_classification": "saas_subscription",
                   "product_description": "Privileged access management and identity security platform",  # noqa: E501
                   "primary_products": [{"name": "Privileged Access Manager",
                                         "type": "saas_subscription",
                                         "description": "PAM solution for securing privileged accounts",  # noqa: E501
                                         },
                                        {"name": "Endpoint Privilege Security",
                                         "type": "saas_subscription",
                                         "description": "Endpoint security and privilege management",  # noqa: E501
                                         },
                                        {"name": "Secrets Management",
                                         "type": "saas_subscription",
                                         "description": "Automated secrets rotation and management",  # noqa: E501
                                         },
                                        {"name": "Identity Security Platform",
                                         "type": "saas_subscription",
                                         "description": "Comprehensive identity security across cloud/hybrid",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 1999 Israel. HQ shifted to Newton MA 2002, back to Israel 2019. Global leader in identity security.\n📍 HQ: Petach-Tikva, Israel | US HQ: Newton, MA (60 Wells Ave, 02459) | Service Area: Global",  # noqa: E501
                   },
                  {"vendor_name": "HEAD ACOUSTICS INC",
                   "industry": "Test & Measurement",
                   "business_model": "B2B Manufacturing & Services",
                   "typical_delivery": "Physical equipment + software + testing services",  # noqa: E501
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Sound, vibration, voice and audio quality testing equipment and services",  # noqa: E501
                   "primary_products": [{"name": "Audio Quality Testing",
                                         "type": "tangible_personal_property",
                                         "description": "Hardware/software for audio device testing",  # noqa: E501
                                         },
                                        {"name": "Voice Quality Testing",
                                         "type": "tangible_personal_property",
                                         "description": "Telecommunications voice quality measurement",  # noqa: E501
                                         },
                                        {"name": "Sound & Vibration Analysis",
                                         "type": "tangible_personal_property",
                                         "description": "Acoustic measurement systems",
                                         },
                                        {"name": "Engineering Services",
                                         "type": "professional_services",
                                         "description": "Audio quality consulting and testing services",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 1986. World leader in sound/vibration measurement. 8 subsidiaries across 36 countries.\n📍 HQ: Herzogenrath, Germany (Ebertstraße 30a) | US Subsidiary: Location TBD | Service Area: Global (US, China, France, India, Italy, Japan, South Korea, UK)",  # noqa: E501
                   },
                  {"vendor_name": "MEDALLIA INC",
                   "industry": "Customer Experience Management",
                   "business_model": "B2B SaaS",
                   "typical_delivery": "Cloud platform",
                   "wa_tax_classification": "saas_subscription",
                   "product_description": "Customer and employee experience management platform",  # noqa: E501
                   "primary_products": [{"name": "Customer Experience Platform",
                                         "type": "saas_subscription",
                                         "description": "CX feedback and analytics platform",  # noqa: E501
                                         },
                                        {"name": "Employee Experience",
                                         "type": "saas_subscription",
                                         "description": "Employee engagement and feedback tools",  # noqa: E501
                                         },
                                        {"name": "Experience Cloud",
                                         "type": "saas_subscription",
                                         "description": "Integrated experience management suite",  # noqa: E501
                                         },
                                        {"name": "Professional Services",
                                         "type": "professional_services",
                                         "description": "CX consulting and implementation",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 2001. Went public 2019. Multiple headquarters strategy.\n📍 HQ: San Francisco, CA | West Coast HQ: Pleasanton, CA | East Coast HQ: Tysons Corner, VA (opened 2025) | Service Area: Global (Buenos Aires, London, Madrid, Mexico City, Paris, Prague, Tel Aviv, Tokyo, Toronto)",  # noqa: E501
                   },
                  {"vendor_name": "SHI INTERNATIONAL CORP",
                   "industry": "IT Solutions & Reseller",
                   "business_model": "B2B IT Distribution",
                   "typical_delivery": "Physical hardware + software + professional services",  # noqa: E501
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "IT infrastructure, cybersecurity, end-user computing products and services",  # noqa: E501
                   "primary_products": [{"name": "IT Hardware",
                                         "type": "tangible_personal_property",
                                         "description": "Computers, servers, networking equipment",  # noqa: E501
                                         },
                                        {"name": "Software Licensing",
                                         "type": "software_license",
                                         "description": "Enterprise software resale and licensing",  # noqa: E501
                                         },
                                        {"name": "Cybersecurity Solutions",
                                         "type": "saas_subscription",
                                         "description": "Security products and services",  # noqa: E501
                                         },
                                        {"name": "IT Services",
                                         "type": "professional_services",
                                         "description": "Integration, deployment, managed services",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "$12.3B revenue 2021. Largest minority/woman-owned business enterprise (MWBE) in US. 305K sq ft integration center.\n📍 HQ: Somerset, NJ (290 Davidson Ave, 08873) | Integration Center: Piscataway, NJ | Service Area: Global (US, Canada, Europe, UK, France, Netherlands, Asia-Pacific: Singapore, Hong Kong, Australia)",  # noqa: E501
                   },
                  {"vendor_name": "SUBEX INC",
                   "industry": "Telecom Analytics",
                   "business_model": "B2B Software",
                   "typical_delivery": "Software platform + professional services",
                   "wa_tax_classification": "saas_subscription",
                   "product_description": "Telecom analytics and digital trust solutions for communication service providers",  # noqa: E501
                   "primary_products": [{"name": "Revenue Assurance",
                                         "type": "saas_subscription",
                                         "description": "Telecom revenue leakage detection",  # noqa: E501
                                         },
                                        {"name": "Fraud Management",
                                         "type": "saas_subscription",
                                         "description": "Telecom fraud prevention and detection",  # noqa: E501
                                         },
                                        {"name": "Partner Management",
                                         "type": "saas_subscription",
                                         "description": "Partner settlement and reconciliation",  # noqa: E501
                                         },
                                        {"name": "Digital Trust",
                                         "type": "saas_subscription",
                                         "description": "Network security and trust products",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 1992. Global telecom analytics leader. Presence across Americas, EMEA, APAC.\n📍 HQ: Bengaluru (Bangalore), Karnataka, India (Pritech Park SEZ, Block-09, 4th Floor, ORR, Bellandur, 560103) | Service Area: Global",  # noqa: E501
                   },
                  {"vendor_name": "ELEMENTAL TECHNOLOGIES LLC",
                   "industry": "Video Processing Software",
                   "business_model": "B2B Software",
                   "typical_delivery": "Software licenses + cloud platform",
                   "wa_tax_classification": "software_license",
                   "product_description": "Video processing software for multi-screen content delivery (now AWS Elemental)",  # noqa: E501
                   "primary_products": [{"name": "Video Processing Software",
                                         "type": "software_license",
                                         "description": "GPU-based video transcoding and processing",  # noqa: E501
                                         },
                                        {"name": "Streaming Solutions",
                                         "type": "saas_subscription",
                                         "description": "Adaptive video streaming over IP networks",  # noqa: E501
                                         },
                                        {"name": "Media Services",
                                         "type": "iaas_paas",
                                         "description": "Cloud-based video workflow services",  # noqa: E501
                                         },
                                        {"name": "Broadcast Solutions",
                                         "type": "software_license",
                                         "description": "Professional broadcast video processing",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 2006. Acquired by Amazon Web Services September 2015 for $350M. Served HBO, ESPN, 700+ media franchises.\n📍 HQ: Portland, OR (1320 SW Broadway Ste 400, 97201) | Service Area: Global (now part of AWS)",  # noqa: E501
                   },
                  {"vendor_name": "TELCORDIA TECHNOLOGIES INC",
                   "industry": "Telecom Software",
                   "business_model": "B2B Software & Services",
                   "typical_delivery": "Software licenses + professional services",
                   "wa_tax_classification": "software_license",
                   "product_description": "Network software and solutions for telecommunications (now iconectiv)",  # noqa: E501
                   "primary_products": [{"name": "Network Management",
                                         "type": "software_license",
                                         "description": "OSS/BSS telecom software",
                                         },
                                        {"name": "Number Portability",
                                         "type": "saas_subscription",
                                         "description": "Telephone number management and portability",  # noqa: E501
                                         },
                                        {"name": "Messaging Solutions",
                                         "type": "saas_subscription",
                                         "description": "SMS, MMS routing and management",  # noqa: E501
                                         },
                                        {"name": "Professional Services",
                                         "type": "professional_services",
                                         "description": "Telecom consulting and integration",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Originally Bellcore (1983), renamed Telcordia 1996. Acquired by Ericsson 2012, rebranded iconectiv 2013. Moved HQ Piscataway to Bridgewater NJ 2017.\n📍 HQ: Bridgewater, NJ (100 Somerset Corporate Blvd, 08807) | Former: Piscataway, NJ (1 Telcordia Drive) | Service Area: Global",  # noqa: E501
                   },
                  {"vendor_name": "PITNEY BOWES SOFTWARE",
                   "industry": "Location Intelligence & Data",
                   "business_model": "B2B Software",
                   "typical_delivery": "Software platform + data services",
                   "wa_tax_classification": "saas_subscription",
                   "product_description": "Location intelligence and data management software (now part of Precisely)",  # noqa: E501
                   "primary_products": [{"name": "Location Intelligence",
                                         "type": "saas_subscription",
                                         "description": "Geospatial data analysis and visualization",  # noqa: E501
                                         },
                                        {"name": "Data Quality",
                                         "type": "saas_subscription",
                                         "description": "Data integrity and enrichment platform",  # noqa: E501
                                         },
                                        {"name": "Address Verification",
                                         "type": "saas_subscription",
                                         "description": "Address validation and geocoding services",  # noqa: E501
                                         },
                                        {"name": "MapInfo",
                                         "type": "software_license",
                                         "description": "Geographic information systems software",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Acquired MapInfo 2007. Software division sold to Syncsort (now Precisely). Corporate HQ Stamford CT, software division Troy NY.\n📍 Software HQ: Troy, NY (One Global View, 12180) | Corporate: Stamford, CT (3001 Summer St, 06926) | Service Area: Global (now part of Precisely)",  # noqa: E501
                   },
                  {"vendor_name": "OPENMARKET INC",
                   "industry": "Mobile Messaging",
                   "business_model": "B2B SaaS",
                   "typical_delivery": "Cloud messaging platform",
                   "wa_tax_classification": "saas_subscription",
                   "product_description": "Mobile messaging and SMS API platform for enterprises",  # noqa: E501
                   "primary_products": [{"name": "SMS API",
                                         "type": "saas_subscription",
                                         "description": "Enterprise SMS messaging API",
                                         },
                                        {"name": "Mobile Messaging",
                                         "type": "saas_subscription",
                                         "description": "Multi-channel mobile messaging platform",  # noqa: E501
                                         },
                                        {"name": "MMS Services",
                                         "type": "saas_subscription",
                                         "description": "Multimedia messaging services",
                                         },
                                        {"name": "Carrier Connectivity",
                                         "type": "saas_subscription",
                                         "description": "Direct carrier connections for messaging",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 1999. Pioneer in mobile messaging for enterprises. Acquired by Amdocs 2013.\n📍 HQ: Seattle, WA area (location historical, now part of Amdocs) | Service Area: Global",  # noqa: E501
                   },
                  {"vendor_name": "AUDIO FIDELITY COMMUNICATIONS",
                   "industry": "Telecommunications Equipment",
                   "business_model": "B2B Equipment Sales",
                   "typical_delivery": "Physical equipment + installation services",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Telecommunications equipment sales and installation services",  # noqa: E501
                   "primary_products": [{"name": "Telecom Equipment",
                                         "type": "tangible_personal_property",
                                         "description": "Phone systems, communication equipment",  # noqa: E501
                                         },
                                        {"name": "Audio Systems",
                                         "type": "tangible_personal_property",
                                         "description": "Commercial audio and PA systems",  # noqa: E501
                                         },
                                        {"name": "Installation Services",
                                         "type": "professional_services",
                                         "description": "Equipment installation and configuration",  # noqa: E501
                                         },
                                        {"name": "Maintenance Services",
                                         "type": "professional_services",
                                         "description": "Ongoing equipment service and support",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Regional telecommunications equipment provider.\n📍 HQ: Location TBD (regional operations) | Service Area: Regional",  # noqa: E501
                   },
                  {"vendor_name": "MAILFINANCE INC",
                   "industry": "Mailing Services & Equipment",
                   "business_model": "B2B Services",
                   "typical_delivery": "Equipment leasing + services",
                   "wa_tax_classification": "professional_services",
                   "product_description": "Postage metering and mailing equipment services",  # noqa: E501
                   "primary_products": [{"name": "Postage Meters",
                                         "type": "tangible_personal_property",
                                         "description": "Postage metering equipment leasing",  # noqa: E501
                                         },
                                        {"name": "Mailing Equipment",
                                         "type": "tangible_personal_property",
                                         "description": "Folders, inserters, sorting equipment",  # noqa: E501
                                         },
                                        {"name": "Mail Services",
                                         "type": "professional_services",
                                         "description": "Mail processing and management services",  # noqa: E501
                                         },
                                        {"name": "Equipment Maintenance",
                                         "type": "professional_services",
                                         "description": "Service and maintenance contracts",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Part of Pitney Bowes mailing equipment and services ecosystem.\n📍 HQ: Location TBD (likely related to Pitney Bowes network) | Service Area: National",  # noqa: E501
                   },
                  {"vendor_name": "LINDGREN RF ENCLOSURES",
                   "industry": "RF Shielding & Testing",
                   "business_model": "B2B Manufacturing",
                   "typical_delivery": "Manufacturing + installation",
                   "wa_tax_classification": "manufacturing",
                   "product_description": "RF shielding enclosures and anechoic chambers for testing",  # noqa: E501
                   "primary_products": [{"name": "RF Shielded Rooms",
                                         "type": "tangible_personal_property",
                                         "description": "Electromagnetic shielding enclosures",  # noqa: E501
                                         },
                                        {"name": "Anechoic Chambers",
                                         "type": "tangible_personal_property",
                                         "description": "RF absorber-lined test chambers",  # noqa: E501
                                         },
                                        {"name": "Test Cells",
                                         "type": "tangible_personal_property",
                                         "description": "Wireless device testing enclosures",  # noqa: E501
                                         },
                                        {"name": "Installation Services",
                                         "type": "construction_services",
                                         "description": "Chamber installation and commissioning",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Part of Ets-Lindgren. Specializes in EMC/RF test chambers and shielding.\n📍 HQ: Cedar Park, TX (as part of Ets-Lindgren) | Service Area: Global",  # noqa: E501
                   },
                  {"vendor_name": "COST SIGN INC",
                   "industry": "Signage Manufacturing",
                   "business_model": "B2B Services",
                   "typical_delivery": "Manufacturing + installation",
                   "wa_tax_classification": "construction_services",
                   "product_description": "Commercial signage manufacturing and installation",  # noqa: E501
                   "primary_products": [{"name": "Commercial Signs",
                                         "type": "tangible_personal_property",
                                         "description": "Interior and exterior signage",
                                         },
                                        {"name": "Installation Services",
                                         "type": "construction_services",
                                         "description": "Sign installation and mounting",  # noqa: E501
                                         },
                                        {"name": "Maintenance Services",
                                         "type": "professional_services",
                                         "description": "Sign repair and maintenance",
                                         },
                                        ],
                   "research_notes": "Regional signage company. Note: Similar to COAST SIGN INCORPORATED (different company).\n📍 HQ: Location TBD (regional) | Service Area: Regional",  # noqa: E501
                   },
                  {"vendor_name": "EMC CORPORATION",
                   "industry": "Data Storage & Information Security",
                   "business_model": "B2B Technology",
                   "typical_delivery": "Physical hardware + software + cloud services",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Data storage, virtualization, cloud computing products (now Dell Technologies)",  # noqa: E501
                   "primary_products": [{"name": "Storage Systems",
                                         "type": "tangible_personal_property",
                                         "description": "Enterprise data storage arrays and systems",  # noqa: E501
                                         },
                                        {"name": "Virtualization Software",
                                         "type": "software_license",
                                         "description": "VMware and virtualization platforms",  # noqa: E501
                                         },
                                        {"name": "Cloud Services",
                                         "type": "iaas_paas",
                                         "description": "Cloud storage and computing services",  # noqa: E501
                                         },
                                        {"name": "Information Security",
                                         "type": "saas_subscription",
                                         "description": "Data protection and security solutions",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 1979 Massachusetts. Merged with Dell 2016 for $67B to form Dell Technologies. EMC².\n📍 HQ: Hopkinton, MA (176 South Street, 01748) | Post-merger: Hopkinton, MA + Round Rock, TX | Service Area: Global",  # noqa: E501
                   },
                  {"vendor_name": "MOBILE TECH INC",
                   "industry": "Mobile Technology Services",
                   "business_model": "B2B Services",
                   "typical_delivery": "On-site services + equipment",
                   "wa_tax_classification": "professional_services",
                   "product_description": "Mobile device services and technology solutions",  # noqa: E501
                   "primary_products": [{"name": "Mobile Device Services",
                                         "type": "professional_services",
                                         "description": "Device configuration and deployment",  # noqa: E501
                                         },
                                        {"name": "Technical Services",
                                         "type": "professional_services",
                                         "description": "IT and mobile technology services",  # noqa: E501
                                         },
                                        {"name": "Equipment",
                                         "type": "tangible_personal_property",
                                         "description": "Mobile technology equipment",
                                         },
                                        ],
                   "research_notes": "Mobile technology services provider.\n📍 HQ: Location TBD | Service Area: Regional",  # noqa: E501
                   },
                  {"vendor_name": "ORACLE AMERICA INC",
                   "industry": "Enterprise Software & Cloud",
                   "business_model": "B2B Software",
                   "typical_delivery": "Software licenses + cloud platform + professional services",  # noqa: E501
                   "wa_tax_classification": "saas_subscription",
                   "product_description": "Enterprise software, database, cloud infrastructure and applications",  # noqa: E501
                   "primary_products": [{"name": "Oracle Database",
                                         "type": "software_license",
                                         "description": "Enterprise database management systems",  # noqa: E501
                                         },
                                        {"name": "Oracle Cloud",
                                         "type": "iaas_paas",
                                         "description": "Cloud infrastructure and platform services",  # noqa: E501
                                         },
                                        {"name": "Enterprise Applications",
                                         "type": "saas_subscription",
                                         "description": "ERP, HCM, CX cloud applications",  # noqa: E501
                                         },
                                        {"name": "Java & Middleware",
                                         "type": "software_license",
                                         "description": "Java platform and middleware software",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 1977. HQ Redwood Shores 1989-2020. Moved to Austin TX 2020, then Nashville TN 2024. Major operations remain in Redwood City.\n📍 HQ: Nashville, TN (2024) | Major Campus: Redwood City, CA (500 Oracle Pkwy, Redwood Shores, 94065) | Former HQ: Austin, TX (2020-2024) | Service Area: Global",  # noqa: E501
                   },
                  {"vendor_name": "KEYSIGHT TECHNOLOGIES INC",
                   "industry": "Test & Measurement Equipment",
                   "business_model": "B2B Manufacturing",
                   "typical_delivery": "Physical equipment + software",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Electronic test and measurement equipment and software",  # noqa: E501
                   "primary_products": [{"name": "Network Test Equipment",
                                         "type": "tangible_personal_property",
                                         "description": "5G/wireless network testing tools",  # noqa: E501
                                         },
                                        {"name": "Electronic Measurement",
                                         "type": "tangible_personal_property",
                                         "description": "Oscilloscopes, signal analyzers, meters",  # noqa: E501
                                         },
                                        {"name": "Test Software",
                                         "type": "software_license",
                                         "description": "Measurement and analysis software",  # noqa: E501
                                         },
                                        {"name": "Services",
                                         "type": "professional_services",
                                         "description": "Calibration, repair, consulting services",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Spun off from Agilent 2014. Agilent inherited from HP Test & Measurement. 1,300 employees Santa Rosa, 10,000 worldwide. Largest company headquartered in Sonoma County.\n📍 HQ: Santa Rosa, CA (1400 Fountaingrove Pkwy, 95403) | Service Area: Global",  # noqa: E501
                   },
                  {"vendor_name": "GENESCO SPORTS ENTERPRISES INC",
                   "industry": "Sports & Recreation",
                   "business_model": "B2B/B2C Retail",
                   "typical_delivery": "Physical retail + distribution",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Sports equipment and apparel retail and distribution",  # noqa: E501
                   "primary_products": [{"name": "Sports Equipment",
                                         "type": "tangible_personal_property",
                                         "description": "Athletic equipment and gear",
                                         },
                                        {"name": "Apparel",
                                         "type": "tangible_personal_property",
                                         "description": "Sports and athletic apparel",
                                         },
                                        {"name": "Footwear",
                                         "type": "tangible_personal_property",
                                         "description": "Athletic shoes and footwear",
                                         },
                                        ],
                   "research_notes": "Part of Genesco retail family. Sports-focused division.\n📍 HQ: Nashville, TN (Genesco parent company) | Service Area: National",  # noqa: E501
                   },
                  {"vendor_name": "CORNELL STOREFRONT SYSTEMS INC",
                   "industry": "Retail Equipment Manufacturing",
                   "business_model": "B2B Manufacturing",
                   "typical_delivery": "Manufacturing + installation",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Rolling steel doors and storefront security systems",  # noqa: E501
                   "primary_products": [{"name": "Rolling Steel Doors",
                                         "type": "tangible_personal_property",
                                         "description": "Commercial rolling doors and shutters",  # noqa: E501
                                         },
                                        {"name": "Security Grilles",
                                         "type": "tangible_personal_property",
                                         "description": "Storefront security grilles and gates",  # noqa: E501
                                         },
                                        {"name": "Installation Services",
                                         "type": "construction_services",
                                         "description": "Door and grille installation",
                                         },
                                        {"name": "Maintenance Services",
                                         "type": "professional_services",
                                         "description": "Service and repair of door systems",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Manufacturer of rolling doors and security systems for retail/commercial.\n📍 HQ: Location TBD (likely Northeast US) | Service Area: National",  # noqa: E501
                   },
                  {"vendor_name": "ADVANCED COLLECTION SERVICES",
                   "industry": "Collections & Financial Services",
                   "business_model": "B2B Services",
                   "typical_delivery": "Professional services",
                   "wa_tax_classification": "professional_services",
                   "product_description": "Debt collection and accounts receivable management services",  # noqa: E501
                   "primary_products": [{"name": "Collections Services",
                                         "type": "professional_services",
                                         "description": "Commercial debt collection services",  # noqa: E501
                                         },
                                        {"name": "AR Management",
                                         "type": "professional_services",
                                         "description": "Accounts receivable management",  # noqa: E501
                                         },
                                        {"name": "Skip Tracing",
                                         "type": "professional_services",
                                         "description": "Debtor location services",
                                         },
                                        {"name": "Reporting Services",
                                         "type": "professional_services",
                                         "description": "Collection reporting and analytics",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Commercial collections agency providing B2B debt recovery services.\n📍 HQ: Location TBD | Service Area: National",  # noqa: E501
                   },
                  {"vendor_name": "SERVICENOW INC",
                   "industry": "Cloud Workflow Automation",
                   "business_model": "B2B SaaS",
                   "typical_delivery": "Cloud platform",
                   "wa_tax_classification": "saas_subscription",
                   "product_description": "Cloud-based workflow automation and IT service management platform",  # noqa: E501
                   "primary_products": [{"name": "IT Service Management",
                                         "type": "saas_subscription",
                                         "description": "ITSM and IT operations management",  # noqa: E501
                                         },
                                        {"name": "HR Service Delivery",
                                         "type": "saas_subscription",
                                         "description": "Employee service management platform",  # noqa: E501
                                         },
                                        {"name": "Customer Service Management",
                                         "type": "saas_subscription",
                                         "description": "Customer service workflow automation",  # noqa: E501
                                         },
                                        {"name": "Now Platform",
                                         "type": "saas_subscription",
                                         "description": "Low-code application development platform",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 2003 by Fred Luddy. IPO 2012. Moved HQ from San Diego to Santa Clara 2012. S&P 100/500 constituent.\n📍 HQ: Santa Clara, CA (2225 Lawson Ln, 95054) | Service Area: Global (76 office locations worldwide)",  # noqa: E501
                   },
                  ]


def update_vendors_batch6_part1():
    """Update first set of Batch 6 vendors"""

    print("Connecting to Supabase...")
    supabase = get_supabase_client()
    print("✓ Connected\n")

    print(f"Updating Batch 6 Part 1: {len(BATCH6_VENDORS)} vendors...\n")

    updated = 0
    errors = 0

    for vendor_data in BATCH6_VENDORS:
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
    print(f"✓ Batch 6 Part 1: {updated}/{len(BATCH6_VENDORS)} vendors updated")
    print(f"❌ Errors: {errors}")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    update_vendors_batch6_part1()
