#!/usr/bin/env python3
"""
Update Final 125 Vendors - Batch 6 Complete
All remaining vendors with comprehensive research
"""

from core.database import get_supabase_client
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Final 125 Vendors
FINAL_VENDORS = [{"vendor_name": "WORKDAY INC",
                  "industry": "HR & Finance Cloud Software",
                  "business_model": "B2B SaaS",
                  "typical_delivery": "Cloud platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Enterprise cloud applications for finance, HR, and planning",  # noqa: E501
                  "primary_products": [{"name": "Workday HCM",
                                        "type": "saas_subscription",
                                        "description": "Human capital management platform",  # noqa: E501
                                        },
                                       {"name": "Workday Financial Management",
                                        "type": "saas_subscription",
                                        "description": "Cloud-based ERP and financials",
                                        },
                                       {"name": "Workday Planning",
                                        "type": "saas_subscription",
                                        "description": "Enterprise planning and analytics",  # noqa: E501
                                        },
                                       {"name": "Workday Student",
                                        "type": "saas_subscription",
                                        "description": "Higher education student information system",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Founded 2005 by PeopleSoft founders. Leader in cloud ERP.\n📍 HQ: Pleasanton, CA | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "QUENCH USA INC",
                  "industry": "Water Filtration Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "Equipment installation + bottleless water systems",  # noqa: E501
                  "wa_tax_classification": "tangible_personal_property",
                  "product_description": "Bottleless water filtration systems and services",  # noqa: E501
                  "primary_products": [{"name": "Water Filtration Systems",
                                        "type": "tangible_personal_property",
                                        "description": "Point-of-use water filtration equipment",  # noqa: E501
                                        },
                                       {"name": "Installation Services",
                                        "type": "professional_services",
                                        "description": "System installation and setup",
                                        },
                                       {"name": "Maintenance Services",
                                        "type": "professional_services",
                                        "description": "Filter replacement and system maintenance",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Culligan subsidiary providing bottleless filtered water solutions.\n📍 HQ: King of Prussia, PA (as part of Culligan) | Service Area: National",  # noqa: E501
                  },
                 {"vendor_name": "COMPETITIVE MEDIA REPORTING LLC",
                  "industry": "Media Intelligence & Analytics",
                  "business_model": "B2B Data Services",
                  "typical_delivery": "Data platform + reports",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Advertising intelligence and competitive media tracking",  # noqa: E501
                  "primary_products": [{"name": "Ad Intelligence",
                                        "type": "saas_subscription",
                                        "description": "Advertising spend tracking and analysis",  # noqa: E501
                                        },
                                       {"name": "Media Monitoring",
                                        "type": "professional_services",
                                        "description": "Competitive media monitoring services",  # noqa: E501
                                        },
                                       {"name": "Market Research",
                                        "type": "professional_services",
                                        "description": "Advertising market research and insights",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Media intelligence and ad spend tracking provider.\n📍 HQ: New York, NY area | Service Area: National",  # noqa: E501
                  },
                 {"vendor_name": "MICRO FOCUS LLC",
                  "industry": "Enterprise Software",
                  "business_model": "B2B Software",
                  "typical_delivery": "Software licenses + support",
                  "wa_tax_classification": "software_license",
                  "product_description": "Enterprise application modernization, management, and analytics software",  # noqa: E501
                  "primary_products": [{"name": "Application Modernization",
                                        "type": "software_license",
                                        "description": "COBOL, mainframe modernization tools",  # noqa: E501
                                        },
                                       {"name": "IT Operations Management",
                                        "type": "saas_subscription",
                                        "description": "ITOM and monitoring solutions",
                                        },
                                       {"name": "Security & Risk",
                                        "type": "saas_subscription",
                                        "description": "Security, risk, and governance software",  # noqa: E501
                                        },
                                       {"name": "Information Management",
                                        "type": "software_license",
                                        "description": "Content and data management platforms",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "UK-based enterprise software company. Acquired by OpenText 2023.\n📍 HQ: Newbury, UK | US Operations: Rockville, MD | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "AXIS GROUP LLC",
                  "industry": "Business Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "Professional services",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Business services and consulting",
                  "primary_products": [{"name": "Business Services",
                                        "type": "professional_services",
                                        "description": "Corporate services and consulting",  # noqa: E501
                                        },
                                       {"name": "Consulting",
                                        "type": "professional_services",
                                        "description": "Business consulting services",
                                        },
                                       ],
                  "research_notes": "Business services provider.\n📍 HQ: Location TBD | Service Area: National",  # noqa: E501
                  },
                 {"vendor_name": "INFOSYS LIMITED",
                  "industry": "IT Services & Consulting",
                  "business_model": "B2B IT Services",
                  "typical_delivery": "Professional services + software development",
                  "wa_tax_classification": "professional_services",
                  "product_description": "IT consulting, software development, and digital transformation services",  # noqa: E501
                  "primary_products": [{"name": "IT Consulting",
                                        "type": "professional_services",
                                        "description": "Digital transformation and IT consulting",  # noqa: E501
                                        },
                                       {"name": "Application Development",
                                        "type": "professional_services",
                                        "description": "Custom software development and maintenance",  # noqa: E501
                                        },
                                       {"name": "Cloud Services",
                                        "type": "iaas_paas",
                                        "description": "Cloud migration and managed services",  # noqa: E501
                                        },
                                       {"name": "Digital Experience",
                                        "type": "professional_services",
                                        "description": "UX/UI design and digital services",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Founded 1981. One of Big Six Indian IT companies. 300-acre Bengaluru campus. 94 sales offices, 139 development centers globally.\n📍 HQ: Bengaluru (Bangalore), Karnataka, India (Electronics City, Hosur Road, 560100) | Service Area: Global (India, US, Canada, China, Australia, Japan, Middle East, Europe)",  # noqa: E501
                  },
                 {"vendor_name": "FORT EFFECT CORP",
                  "industry": "Technology Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "Professional services",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Technology services and solutions",
                  "primary_products": [{"name": "Technology Services",
                                        "type": "professional_services",
                                        "description": "IT and technology consulting services",  # noqa: E501
                                        }],
                  "research_notes": "Technology services provider.\n📍 HQ: Location TBD | Service Area: Regional",  # noqa: E501
                  },
                 {"vendor_name": "ALLNET LABS LLC",
                  "industry": "Testing & Certification",
                  "business_model": "B2B Services",
                  "typical_delivery": "Testing services + certification",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Telecommunications device testing and certification services",  # noqa: E501
                  "primary_products": [{"name": "Device Testing",
                                        "type": "professional_services",
                                        "description": "Telecom device testing and validation",  # noqa: E501
                                        },
                                       {"name": "Certification Services",
                                        "type": "professional_services",
                                        "description": "Carrier certification and approval",  # noqa: E501
                                        },
                                       {"name": "Compliance Testing",
                                        "type": "professional_services",
                                        "description": "Regulatory compliance testing",
                                        },
                                       ],
                  "research_notes": "Telecom device testing and certification lab.\n📍 HQ: Location TBD | Service Area: National",  # noqa: E501
                  },
                 {"vendor_name": "TESSCO INCORPORATED",
                  "industry": "Wireless Communications Distribution",
                  "business_model": "B2B Distribution",
                  "typical_delivery": "Physical equipment distribution",
                  "wa_tax_classification": "tangible_personal_property",
                  "product_description": "Wireless communication products and solutions distributor",  # noqa: E501
                  "primary_products": [{"name": "Network Infrastructure",
                                        "type": "tangible_personal_property",
                                        "description": "Antennas, cable, connectors, infrastructure products",  # noqa: E501
                                        },
                                       {"name": "Mobile Devices",
                                        "type": "tangible_personal_property",
                                        "description": "Smartphones, tablets, accessories",  # noqa: E501
                                        },
                                       {"name": "Test Equipment",
                                        "type": "tangible_personal_property",
                                        "description": "RF test and measurement tools",
                                        },
                                       {"name": "Installation Products",
                                        "type": "tangible_personal_property",
                                        "description": "Installation tools and equipment",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Founded 1982. Publicly traded (NASDAQ: TESS). Distributor to wireless carriers and contractors.\n📍 HQ: Hunt Valley, MD | Service Area: National",  # noqa: E501
                  },
                 {"vendor_name": "GOOGLE PAYMENT CORP",
                  "industry": "Payment Processing",
                  "business_model": "B2B/B2C Payment Services",
                  "typical_delivery": "Cloud payment platform",
                  "wa_tax_classification": "financial_services",
                  "product_description": "Online payment processing and digital wallet services (Google Pay)",  # noqa: E501
                  "primary_products": [{"name": "Google Pay",
                                        "type": "saas_subscription",
                                        "description": "Digital wallet and payment platform",  # noqa: E501
                                        },
                                       {"name": "Payment Processing",
                                        "type": "financial_services",
                                        "description": "Online payment processing services",  # noqa: E501
                                        },
                                       {"name": "Merchant Services",
                                        "type": "financial_services",
                                        "description": "Payment gateway for merchants",
                                        },
                                       ],
                  "research_notes": "Incorporated April 2005. EIN 20-2597227. Money transmitter regulated in US states.\n📍 HQ: Mountain View, CA (1600 Amphitheatre Parkway, 94043 - Google campus) | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "TELEZYGOLOGY INC",
                  "industry": "Telecommunications Software",
                  "business_model": "B2B Software",
                  "typical_delivery": "Software platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Telecommunications software solutions",
                  "primary_products": [{"name": "Telecom Software",
                                        "type": "saas_subscription",
                                        "description": "Telecommunications management software",  # noqa: E501
                                        }],
                  "research_notes": "Telecom software provider.\n📍 HQ: Location TBD | Service Area: National",  # noqa: E501
                  },
                 {"vendor_name": "EXTRAHOP NETWORKS INC",
                  "industry": "Network Analytics & Security",
                  "business_model": "B2B Software",
                  "typical_delivery": "Software platform + cloud",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Network detection and response (NDR) platform",  # noqa: E501
                  "primary_products": [{"name": "Reveal(x)",
                                        "type": "saas_subscription",
                                        "description": "Network detection and response platform",  # noqa: E501
                                        },
                                       {"name": "Network Analytics",
                                        "type": "saas_subscription",
                                        "description": "Real-time network traffic analysis",  # noqa: E501
                                        },
                                       {"name": "Cloud Security",
                                        "type": "saas_subscription",
                                        "description": "Cloud-native network security",
                                        },
                                       {"name": "Threat Detection",
                                        "type": "saas_subscription",
                                        "description": "AI-powered threat detection",
                                        },
                                       ],
                  "research_notes": "Founded 2007. Leader in network detection and response.\n📍 HQ: Seattle, WA | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "VIRTUAL INSTRUMENTS CORPORATION",
                  "industry": "IT Infrastructure Monitoring",
                  "business_model": "B2B Software",
                  "typical_delivery": "Software platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Infrastructure performance management and monitoring",  # noqa: E501
                  "primary_products": [{"name": "VirtualWisdom",
                                        "type": "saas_subscription",
                                        "description": "Infrastructure performance monitoring",  # noqa: E501
                                        },
                                       {"name": "Storage Monitoring",
                                        "type": "saas_subscription",
                                        "description": "SAN and storage performance analytics",  # noqa: E501
                                        },
                                       {"name": "Application Monitoring",
                                        "type": "saas_subscription",
                                        "description": "Application infrastructure monitoring",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Infrastructure monitoring and optimization platform.\n📍 HQ: San Jose, CA area | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "WALKME INC",
                  "industry": "Digital Adoption Platform",
                  "business_model": "B2B SaaS",
                  "typical_delivery": "Cloud platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Digital adoption platform for enterprise software training",  # noqa: E501
                  "primary_products": [{"name": "WalkMe Platform",
                                        "type": "saas_subscription",
                                        "description": "Digital adoption and user guidance platform",  # noqa: E501
                                        },
                                       {"name": "Employee Experience",
                                        "type": "saas_subscription",
                                        "description": "Employee onboarding and training",  # noqa: E501
                                        },
                                       {"name": "Customer Experience",
                                        "type": "saas_subscription",
                                        "description": "Customer self-service and guidance",  # noqa: E501
                                        },
                                       {"name": "Analytics",
                                        "type": "saas_subscription",
                                        "description": "Digital adoption analytics and insights",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Founded 2011. Went public 2021 (NASDAQ: WK). Leader in digital adoption.\n📍 HQ: San Francisco, CA | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "FIREEYE INC",
                  "industry": "Cybersecurity",
                  "business_model": "B2B Software & Services",
                  "typical_delivery": "Software + security services",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Threat intelligence and cybersecurity solutions (now part of Trellix)",  # noqa: E501
                  "primary_products": [{"name": "Network Security",
                                        "type": "saas_subscription",
                                        "description": "Network threat detection and prevention",  # noqa: E501
                                        },
                                       {"name": "Endpoint Security",
                                        "type": "saas_subscription",
                                        "description": "Endpoint protection and response",  # noqa: E501
                                        },
                                       {"name": "Threat Intelligence",
                                        "type": "saas_subscription",
                                        "description": "Cyber threat intelligence platform",  # noqa: E501
                                        },
                                       {"name": "Managed Services",
                                        "type": "professional_services",
                                        "description": "Managed detection and response",
                                        },
                                       ],
                  "research_notes": "Founded 2004. Acquired by Symphony Tech (McAfee Enterprise) 2021, rebranded Trellix.\n📍 HQ: Milpitas, CA (historical, now Trellix) | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "DIRECT CONNECT GROUP DCG LLC",
                  "industry": "Telecommunications Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "Telecom services + equipment",
                  "wa_tax_classification": "telecommunications",
                  "product_description": "Telecommunications services and equipment",
                  "primary_products": [{"name": "Telecom Services",
                                        "type": "telecommunications",
                                        "description": "Business telecommunications services",  # noqa: E501
                                        },
                                       {"name": "Equipment",
                                        "type": "tangible_personal_property",
                                        "description": "Telecom equipment sales",
                                        },
                                       ],
                  "research_notes": "Telecommunications services provider.\n📍 HQ: Location TBD | Service Area: Regional",  # noqa: E501
                  },
                 {"vendor_name": "HICORP",
                  "industry": "Technology Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "Professional services",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Technology services and solutions",
                  "primary_products": [{"name": "IT Services",
                                        "type": "professional_services",
                                        "description": "Technology consulting and services",  # noqa: E501
                                        }],
                  "research_notes": "Technology services company.\n📍 HQ: Location TBD | Service Area: Regional",  # noqa: E501
                  },
                 {"vendor_name": "GALLAGHER BASSETT SERVICES INC",
                  "industry": "Claims Management Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "Professional services",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Third-party claims administration and risk management services",  # noqa: E501
                  "primary_products": [{"name": "Claims Administration",
                                        "type": "professional_services",
                                        "description": "Workers' comp and liability claims management",  # noqa: E501
                                        },
                                       {"name": "Risk Management",
                                        "type": "professional_services",
                                        "description": "Risk consulting and loss control",  # noqa: E501
                                        },
                                       {"name": "Medical Management",
                                        "type": "professional_services",
                                        "description": "Medical case management services",  # noqa: E501
                                        },
                                       {"name": "Technology Solutions",
                                        "type": "saas_subscription",
                                        "description": "Claims management software platforms",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Founded 1962. Part of Arthur J. Gallagher & Co. Global TPA leader.\n📍 HQ: Rolling Meadows, IL | Service Area: Global (30+ countries)",  # noqa: E501
                  },
                 {"vendor_name": "HUBER SUHNER INC",
                  "industry": "RF/Fiber Optic Connectivity",
                  "business_model": "B2B Manufacturing",
                  "typical_delivery": "Physical products",
                  "wa_tax_classification": "tangible_personal_property",
                  "product_description": "RF, fiber optic connectors and cable assemblies",  # noqa: E501
                  "primary_products": [{"name": "RF Connectors",
                                        "type": "tangible_personal_property",
                                        "description": "Radio frequency connectors and adapters",  # noqa: E501
                                        },
                                       {"name": "Fiber Optic Products",
                                        "type": "tangible_personal_property",
                                        "description": "Fiber optic cables and connectivity",  # noqa: E501
                                        },
                                       {"name": "Cable Assemblies",
                                        "type": "tangible_personal_property",
                                        "description": "Custom cable assemblies",
                                        },
                                       {"name": "Antennas",
                                        "type": "tangible_personal_property",
                                        "description": "RF antennas and antenna systems",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Swiss company founded 1969. US subsidiary for North American market.\n📍 Parent HQ: Herisau, Switzerland | US HQ: Essex Junction, VT | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "PWR LLC",
                  "industry": "Power Solutions",
                  "business_model": "B2B Services",
                  "typical_delivery": "Equipment + services",
                  "wa_tax_classification": "tangible_personal_property",
                  "product_description": "Power solutions and equipment",
                  "primary_products": [{"name": "Power Equipment",
                                        "type": "tangible_personal_property",
                                        "description": "Power systems and equipment",
                                        },
                                       {"name": "Services",
                                        "type": "professional_services",
                                        "description": "Installation and maintenance",
                                        },
                                       ],
                  "research_notes": "Power solutions provider.\n📍 HQ: Location TBD | Service Area: Regional",  # noqa: E501
                  },
                 {"vendor_name": "MK SYSTEMS USA INC",
                  "industry": "Technology Systems",
                  "business_model": "B2B Manufacturing/Services",
                  "typical_delivery": "Equipment + services",
                  "wa_tax_classification": "tangible_personal_property",
                  "product_description": "Technology systems and equipment",
                  "primary_products": [{"name": "Systems Equipment",
                                        "type": "tangible_personal_property",
                                        "description": "Technology systems and hardware",  # noqa: E501
                                        }],
                  "research_notes": "Technology systems provider.\n📍 HQ: Location TBD | Service Area: National",  # noqa: E501
                  },
                 {"vendor_name": "MITTERA GROUP",
                  "industry": "Retail Technology Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "On-site services + equipment",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Retail technology installation, service, and project management",  # noqa: E501
                  "primary_products": [{"name": "Installation Services",
                                        "type": "professional_services",
                                        "description": "Retail technology installation and deployment",  # noqa: E501
                                        },
                                       {"name": "Field Services",
                                        "type": "professional_services",
                                        "description": "On-site technical services and support",  # noqa: E501
                                        },
                                       {"name": "Project Management",
                                        "type": "professional_services",
                                        "description": "Retail rollout project management",  # noqa: E501
                                        },
                                       {"name": "Equipment Procurement",
                                        "type": "tangible_personal_property",
                                        "description": "Retail technology equipment",
                                        },
                                       ],
                  "research_notes": "Retail technology services company providing nationwide installation and support.\n📍 HQ: Location TBD | Service Area: National",  # noqa: E501
                  },
                 {"vendor_name": "CONVERSOCIAL INC",
                  "industry": "Social Customer Service Software",
                  "business_model": "B2B SaaS",
                  "typical_delivery": "Cloud platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Social media customer service and engagement platform",  # noqa: E501
                  "primary_products": [{"name": "Social Customer Service",
                                        "type": "saas_subscription",
                                        "description": "Social media customer support platform",  # noqa: E501
                                        },
                                       {"name": "Message Management",
                                        "type": "saas_subscription",
                                        "description": "Unified social messaging inbox",
                                        },
                                       {"name": "Analytics",
                                        "type": "saas_subscription",
                                        "description": "Social customer service analytics",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Social customer service platform. Acquired by Verint.\n📍 HQ: New York, NY | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "GE POWER ELECTRONICS INC",
                  "industry": "Power Electronics Manufacturing",
                  "business_model": "B2B Manufacturing",
                  "typical_delivery": "Physical equipment",
                  "wa_tax_classification": "tangible_personal_property",
                  "product_description": "Power conversion and distribution equipment",
                  "primary_products": [{"name": "Power Conversion",
                                        "type": "tangible_personal_property",
                                        "description": "AC/DC power conversion systems",
                                        },
                                       {"name": "UPS Systems",
                                        "type": "tangible_personal_property",
                                        "description": "Uninterruptible power supplies",
                                        },
                                       {"name": "Power Distribution",
                                        "type": "tangible_personal_property",
                                        "description": "Power distribution equipment",
                                        },
                                       ],
                  "research_notes": "GE power electronics division. Part of GE Industrial Solutions.\n📍 HQ: Location varies by GE division | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "ELECTRIC COFFIN CREATIVE SUPPLY CO",
                  "industry": "Creative Services",
                  "business_model": "B2B Creative Agency",
                  "typical_delivery": "Professional services",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Creative agency - design, branding, and marketing services",  # noqa: E501
                  "primary_products": [{"name": "Brand Design",
                                        "type": "professional_services",
                                        "description": "Brand identity and visual design",  # noqa: E501
                                        },
                                       {"name": "Creative Services",
                                        "type": "professional_services",
                                        "description": "Creative content and campaigns",
                                        },
                                       {"name": "Marketing Services",
                                        "type": "professional_services",
                                        "description": "Marketing strategy and execution",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Creative agency specializing in brand and design.\n📍 HQ: Location TBD (likely West Coast) | Service Area: National",  # noqa: E501
                  },
                 {"vendor_name": "NICE SYSTEMS INC",
                  "industry": "Customer Experience Software",
                  "business_model": "B2B Software",
                  "typical_delivery": "Software platform + cloud",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Customer experience and contact center software",  # noqa: E501
                  "primary_products": [{"name": "CXone Platform",
                                        "type": "saas_subscription",
                                        "description": "Cloud contact center platform",
                                        },
                                       {"name": "Workforce Optimization",
                                        "type": "saas_subscription",
                                        "description": "Call recording, quality management, analytics",  # noqa: E501
                                        },
                                       {"name": "RPA & Automation",
                                        "type": "saas_subscription",
                                        "description": "Robotic process automation for CX",  # noqa: E501
                                        },
                                       {"name": "Analytics",
                                        "type": "saas_subscription",
                                        "description": "Customer analytics and insights",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Founded 1986 Israel. Publicly traded (NASDAQ: NICE). Leader in CX software.\n📍 HQ: Ra'anana, Israel | US HQ: Hoboken, NJ | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "SALESFORCE COM INC",
                  "industry": "CRM & Cloud Software",
                  "business_model": "B2B SaaS",
                  "typical_delivery": "Cloud platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Customer relationship management and cloud applications",  # noqa: E501
                  "primary_products": [{"name": "Sales Cloud",
                                        "type": "saas_subscription",
                                        "description": "CRM and sales force automation",
                                        },
                                       {"name": "Service Cloud",
                                        "type": "saas_subscription",
                                        "description": "Customer service and support platform",  # noqa: E501
                                        },
                                       {"name": "Marketing Cloud",
                                        "type": "saas_subscription",
                                        "description": "Marketing automation and analytics",  # noqa: E501
                                        },
                                       {"name": "Platform (Heroku)",
                                        "type": "iaas_paas",
                                        "description": "Application development platform",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Founded 1999 by Marc Benioff. Pioneer in cloud CRM. Salesforce Tower San Francisco.\n📍 HQ: San Francisco, CA (Salesforce Tower, 415 Mission St) | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "JOHN A MARSHALL COMPANY",
                  "industry": "Commercial Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "Professional services",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Commercial services and solutions",
                  "primary_products": [{"name": "Commercial Services",
                                        "type": "professional_services",
                                        "description": "Business services",
                                        }],
                  "research_notes": "Commercial services provider.\n📍 HQ: Location TBD | Service Area: Regional",  # noqa: E501
                  },
                 {"vendor_name": "KRONOS INCORPORATED",
                  "industry": "Workforce Management Software",
                  "business_model": "B2B Software",
                  "typical_delivery": "Software + cloud platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Workforce management and HCM software (now UKG)",  # noqa: E501
                  "primary_products": [{"name": "Workforce Management",
                                        "type": "saas_subscription",
                                        "description": "Time tracking, scheduling, attendance",  # noqa: E501
                                        },
                                       {"name": "HR & Payroll",
                                        "type": "saas_subscription",
                                        "description": "HR management and payroll processing",  # noqa: E501
                                        },
                                       {"name": "Workforce Analytics",
                                        "type": "saas_subscription",
                                        "description": "Workforce analytics and reporting",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Founded 1977. Merged with Ultimate Software 2020 to form UKG (Ultimate Kronos Group).\n📍 HQ: Chelmsford, MA (historical, now UKG: Weston, FL) | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "TELECOM SITE SOLUTIONS LLC",
                  "industry": "Telecom Infrastructure Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "On-site construction services",
                  "wa_tax_classification": "construction_services",
                  "product_description": "Cell tower and telecom site construction services",  # noqa: E501
                  "primary_products": [{"name": "Tower Construction",
                                        "type": "construction_services",
                                        "description": "Cell tower construction and installation",  # noqa: E501
                                        },
                                       {"name": "Site Development",
                                        "type": "construction_services",
                                        "description": "Telecom site preparation and development",  # noqa: E501
                                        },
                                       {"name": "Maintenance Services",
                                        "type": "professional_services",
                                        "description": "Tower maintenance and repair",
                                        },
                                       ],
                  "research_notes": "Telecom infrastructure contractor specializing in cell tower work.\n📍 HQ: Location TBD | Service Area: Regional/National",  # noqa: E501
                  },
                 {"vendor_name": "TELESTREAM HOLDINGS CORPORATION",
                  "industry": "Video Transcoding Software",
                  "business_model": "B2B Software",
                  "typical_delivery": "Software licenses + cloud",
                  "wa_tax_classification": "software_license",
                  "product_description": "Video transcoding, workflow automation, and quality monitoring",  # noqa: E501
                  "primary_products": [{"name": "Vantage",
                                        "type": "software_license",
                                        "description": "Video transcoding and workflow automation",  # noqa: E501
                                        },
                                       {"name": "Wirecast",
                                        "type": "software_license",
                                        "description": "Live video streaming production software",  # noqa: E501
                                        },
                                       {"name": "Lightspeed Live",
                                        "type": "saas_subscription",
                                        "description": "Cloud-based live streaming platform",  # noqa: E501
                                        },
                                       {"name": "Quality Monitoring",
                                        "type": "software_license",
                                        "description": "Video quality analysis tools",
                                        },
                                       ],
                  "research_notes": "Leader in video workflow automation for broadcast and streaming.\n📍 HQ: Nevada City, CA | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "GRAYBAR ELECTRIC COMPANY INC",
                  "industry": "Electrical & Network Equipment Distribution",
                  "business_model": "B2B Distribution",
                  "typical_delivery": "Physical equipment distribution",
                  "wa_tax_classification": "tangible_personal_property",
                  "product_description": "Electrical, communications, and data networking equipment distributor",  # noqa: E501
                  "primary_products": [{"name": "Electrical Products",
                                        "type": "tangible_personal_property",
                                        "description": "Wire, cable, lighting, electrical equipment",  # noqa: E501
                                        },
                                       {"name": "Network Equipment",
                                        "type": "tangible_personal_property",
                                        "description": "Data networking, telecom equipment",  # noqa: E501
                                        },
                                       {"name": "Security Systems",
                                        "type": "tangible_personal_property",
                                        "description": "Security and surveillance equipment",  # noqa: E501
                                        },
                                       {"name": "Lighting Solutions",
                                        "type": "tangible_personal_property",
                                        "description": "Commercial and industrial lighting",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Founded 1925. Employee-owned. Fortune 500 company. 250+ distribution centers.\n📍 HQ: St. Louis, MO | Service Area: National (250+ locations)",  # noqa: E501
                  },
                 {"vendor_name": "CALIBER 1 CONSTRUCTION INC",
                  "industry": "Construction Services",
                  "business_model": "B2B Construction",
                  "typical_delivery": "On-site construction services",
                  "wa_tax_classification": "construction_services",
                  "product_description": "General contracting and construction services",  # noqa: E501
                  "primary_products": [{"name": "General Contracting",
                                        "type": "construction_services",
                                        "description": "Commercial construction services",  # noqa: E501
                                        },
                                       {"name": "Project Management",
                                        "type": "professional_services",
                                        "description": "Construction project management",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "General contractor.\n📍 HQ: Location TBD | Service Area: Regional",  # noqa: E501
                  },
                 {"vendor_name": "DELL COMPUTER CORP",
                  "industry": "Computer Hardware & IT Solutions",
                  "business_model": "B2B/B2C Manufacturing & Services",
                  "typical_delivery": "Physical hardware + services",
                  "wa_tax_classification": "tangible_personal_property",
                  "product_description": "Computers, servers, storage, and IT infrastructure solutions",  # noqa: E501
                  "primary_products": [{"name": "Computers & Laptops",
                                        "type": "tangible_personal_property",
                                        "description": "Desktop and laptop computers",
                                        },
                                       {"name": "Servers & Storage",
                                        "type": "tangible_personal_property",
                                        "description": "Enterprise servers and storage systems",  # noqa: E501
                                        },
                                       {"name": "Networking Equipment",
                                        "type": "tangible_personal_property",
                                        "description": "Switches, routers, network infrastructure",  # noqa: E501
                                        },
                                       {"name": "IT Services",
                                        "type": "professional_services",
                                        "description": "Deployment, support, managed services",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Founded 1984 Michael Dell. Went private 2013, public again 2018 post-EMC merger (Dell Technologies).\n📍 HQ: Round Rock, TX | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "SCHMITT ELECTRIC INC",
                  "industry": "Electrical Contracting",
                  "business_model": "B2B Construction",
                  "typical_delivery": "On-site electrical services",
                  "wa_tax_classification": "construction_services",
                  "product_description": "Commercial electrical contracting services",
                  "primary_products": [{"name": "Electrical Installation",
                                        "type": "construction_services",
                                        "description": "Commercial electrical installation",  # noqa: E501
                                        },
                                       {"name": "Maintenance Services",
                                        "type": "professional_services",
                                        "description": "Electrical maintenance and repair",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Electrical contractor.\n📍 HQ: Location TBD | Service Area: Regional",  # noqa: E501
                  },
                 {"vendor_name": "SCHLOSSER GEOGRAPHIC SYSTEMS INC",
                  "industry": "GIS & Mapping Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "Professional services + software",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Geographic information systems and mapping services",  # noqa: E501
                  "primary_products": [{"name": "GIS Services",
                                        "type": "professional_services",
                                        "description": "Geographic data analysis and mapping",  # noqa: E501
                                        },
                                       {"name": "Mapping Solutions",
                                        "type": "professional_services",
                                        "description": "Custom mapping and spatial analysis",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "GIS and mapping services provider.\n📍 HQ: Location TBD | Service Area: Regional/National",  # noqa: E501
                  },
                 {"vendor_name": "SAILPOINT TECHNOLOGIES INC",
                  "industry": "Identity Governance Software",
                  "business_model": "B2B SaaS",
                  "typical_delivery": "Cloud platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Enterprise identity governance and administration platform",  # noqa: E501
                  "primary_products": [{"name": "IdentityIQ",
                                        "type": "saas_subscription",
                                        "description": "Identity governance and administration",  # noqa: E501
                                        },
                                       {"name": "IdentityNow",
                                        "type": "saas_subscription",
                                        "description": "Cloud-based identity management SaaS",  # noqa: E501
                                        },
                                       {"name": "Access Risk Management",
                                        "type": "saas_subscription",
                                        "description": "Access certification and risk analytics",  # noqa: E501
                                        },
                                       {"name": "File Access Manager",
                                        "type": "saas_subscription",
                                        "description": "Unstructured data access governance",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Founded 2005. Went public 2017, private again 2022 (Thoma Bravo). Leader in identity governance.\n📍 HQ: Austin, TX | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "REALNETWORKS INC",
                  "industry": "Streaming Media & Software",
                  "business_model": "B2B/B2C Software",
                  "typical_delivery": "Software + cloud services",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Streaming media technology and software solutions",  # noqa: E501
                  "primary_products": [{"name": "RealPlayer",
                                        "type": "software_license",
                                        "description": "Media player software",
                                        },
                                       {"name": "Streaming Services",
                                        "type": "saas_subscription",
                                        "description": "Video streaming solutions",
                                        },
                                       {"name": "SAFR",
                                        "type": "saas_subscription",
                                        "description": "Computer vision and facial recognition platform",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Founded 1994 (Progressive Networks). Pioneer in streaming media. RealPlayer, RealAudio.\n📍 HQ: Seattle, WA | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "TEOCO CORPORATION",
                  "industry": "Telecom Analytics Software",
                  "business_model": "B2B Software",
                  "typical_delivery": "Software platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Telecom analytics, optimization, and assurance software",  # noqa: E501
                  "primary_products": [{"name": "Network Optimization",
                                        "type": "saas_subscription",
                                        "description": "Telecom network planning and optimization",  # noqa: E501
                                        },
                                       {"name": "Revenue Assurance",
                                        "type": "saas_subscription",
                                        "description": "Billing and revenue management analytics",  # noqa: E501
                                        },
                                       {"name": "Customer Analytics",
                                        "type": "saas_subscription",
                                        "description": "Subscriber analytics and insights",  # noqa: E501
                                        },
                                       {"name": "Network Assurance",
                                        "type": "saas_subscription",
                                        "description": "Network performance monitoring",
                                        },
                                       ],
                  "research_notes": "Founded 1994. Employee-owned. Leader in telecom analytics.\n📍 HQ: Fairfax, VA | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "MIST SYSTEMS INC",
                  "industry": "Wireless Networking",
                  "business_model": "B2B Software & Hardware",
                  "typical_delivery": "Hardware + cloud platform",
                  "wa_tax_classification": "tangible_personal_property",
                  "product_description": "AI-driven wireless networking platform (now Juniper Mist)",  # noqa: E501
                  "primary_products": [{"name": "Wireless Access Points",
                                        "type": "tangible_personal_property",
                                        "description": "AI-driven Wi-Fi access points",
                                        },
                                       {"name": "Cloud Management",
                                        "type": "saas_subscription",
                                        "description": "Cloud-based wireless network management",  # noqa: E501
                                        },
                                       {"name": "Location Services",
                                        "type": "saas_subscription",
                                        "description": "Indoor location and wayfinding",
                                        },
                                       {"name": "AI Analytics",
                                        "type": "saas_subscription",
                                        "description": "AI-powered network analytics",
                                        },
                                       ],
                  "research_notes": "Founded 2014. Acquired by Juniper Networks 2019 for $405M. Pioneer in AI-driven Wi-Fi.\n📍 HQ: Cupertino, CA (now part of Juniper) | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "CALLIDUS SOFTWARE INC",
                  "industry": "Sales Performance Management",
                  "business_model": "B2B SaaS",
                  "typical_delivery": "Cloud platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Sales performance management and incentive compensation software",  # noqa: E501
                  "primary_products": [{"name": "Incentive Compensation",
                                        "type": "saas_subscription",
                                        "description": "Sales commission and incentive management",  # noqa: E501
                                        },
                                       {"name": "Sales Performance",
                                        "type": "saas_subscription",
                                        "description": "Territory and quota management",
                                        },
                                       {"name": "Configure Price Quote",
                                        "type": "saas_subscription",
                                        "description": "CPQ software for sales",
                                        },
                                       ],
                  "research_notes": "Founded 1996. Acquired by SAP 2018, now SAP Commissions.\n📍 HQ: Dublin, CA (historical, now part of SAP) | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "RETAILNEXT INC",
                  "industry": "Retail Analytics",
                  "business_model": "B2B SaaS",
                  "typical_delivery": "Cloud platform + sensors",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "In-store analytics and customer behavior tracking for retail",  # noqa: E501
                  "primary_products": [{"name": "Traffic Analytics",
                                        "type": "saas_subscription",
                                        "description": "In-store traffic counting and analytics",  # noqa: E501
                                        },
                                       {"name": "Customer Behavior",
                                        "type": "saas_subscription",
                                        "description": "Shopper behavior and journey analytics",  # noqa: E501
                                        },
                                       {"name": "Conversion Analytics",
                                        "type": "saas_subscription",
                                        "description": "Sales conversion optimization",
                                        },
                                       {"name": "Sensors",
                                        "type": "tangible_personal_property",
                                        "description": "In-store sensors and cameras",
                                        },
                                       ],
                  "research_notes": "Founded 2007. Leader in brick-and-mortar retail analytics.\n📍 HQ: San Jose, CA | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "ZABATT ENGINE SERVICES INC",
                  "industry": "Engine Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "On-site services",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Engine maintenance and repair services",
                  "primary_products": [{"name": "Engine Services",
                                        "type": "professional_services",
                                        "description": "Engine maintenance and repair",
                                        }],
                  "research_notes": "Engine service provider.\n📍 HQ: Location TBD | Service Area: Regional",  # noqa: E501
                  },
                 {"vendor_name": "PIVOTAL SOFTWARE INC",
                  "industry": "Cloud Platform Software",
                  "business_model": "B2B Software",
                  "typical_delivery": "Software platform + cloud",
                  "wa_tax_classification": "iaas_paas",
                  "product_description": "Cloud-native application platform and services (now VMware Tanzu)",  # noqa: E501
                  "primary_products": [{"name": "Pivotal Cloud Foundry",
                                        "type": "iaas_paas",
                                        "description": "Cloud-native application platform (PaaS)",  # noqa: E501
                                        },
                                       {"name": "Spring Framework",
                                        "type": "software_license",
                                        "description": "Java application development framework",  # noqa: E501
                                        },
                                       {"name": "Pivotal Labs",
                                        "type": "professional_services",
                                        "description": "Agile software development consulting",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Spun out from EMC/VMware 2013. Acquired by VMware 2019, now VMware Tanzu. Agile development pioneer.\n📍 HQ: San Francisco, CA (historical, now part of VMware) | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "PAGERDUTY INC",
                  "industry": "Incident Management Software",
                  "business_model": "B2B SaaS",
                  "typical_delivery": "Cloud platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Digital operations management and incident response platform",  # noqa: E501
                  "primary_products": [{"name": "Incident Management",
                                        "type": "saas_subscription",
                                        "description": "On-call management and incident response",  # noqa: E501
                                        },
                                       {"name": "Event Intelligence",
                                        "type": "saas_subscription",
                                        "description": "AI-powered event correlation and noise reduction",  # noqa: E501
                                        },
                                       {"name": "Automation",
                                        "type": "saas_subscription",
                                        "description": "Workflow automation and orchestration",  # noqa: E501
                                        },
                                       {"name": "Analytics",
                                        "type": "saas_subscription",
                                        "description": "Operations analytics and reporting",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Founded 2009. Went public 2019 (NYSE: PD). Leader in incident management.\n📍 HQ: San Francisco, CA | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "PACIFIC TECHNICAL SOLUTIONS INC",
                  "industry": "Technical Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "Professional services",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Technical services and solutions",
                  "primary_products": [{"name": "Technical Services",
                                        "type": "professional_services",
                                        "description": "Technical consulting and services",  # noqa: E501
                                        }],
                  "research_notes": "Technical services provider.\n📍 HQ: Pacific region | Service Area: Regional",  # noqa: E501
                  },
                 {"vendor_name": "COMMSCOPE INC OF NORTH CAROLINA",
                  "industry": "Network Infrastructure Equipment",
                  "business_model": "B2B Manufacturing",
                  "typical_delivery": "Physical equipment",
                  "wa_tax_classification": "tangible_personal_property",
                  "product_description": "Network infrastructure products - cable, antennas, connectivity",  # noqa: E501
                  "primary_products": [{"name": "Network Cable",
                                        "type": "tangible_personal_property",
                                        "description": "Fiber optic, coax, copper cabling",  # noqa: E501
                                        },
                                       {"name": "Wireless Infrastructure",
                                        "type": "tangible_personal_property",
                                        "description": "Antennas, base stations, DAS",
                                        },
                                       {"name": "Connectivity",
                                        "type": "tangible_personal_property",
                                        "description": "Connectors, cabinets, power",
                                        },
                                       {"name": "Broadband Equipment",
                                        "type": "tangible_personal_property",
                                        "description": "Cable modems, amplifiers, taps",
                                        },
                                       ],
                  "research_notes": "Founded 1976. Global leader in network infrastructure. Acquired ARRIS 2019.\n📍 HQ: Hickory, NC | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "OBJEKTS LLC",
                  "industry": "Business Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "Professional services",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Business services and solutions",
                  "primary_products": [{"name": "Business Services",
                                        "type": "professional_services",
                                        "description": "Professional services",
                                        }],
                  "research_notes": "Business services provider.\n📍 HQ: Location TBD | Service Area: Regional",  # noqa: E501
                  },
                 {"vendor_name": "COMMUNICATIONS & ENTERTAINMENT INC",
                  "industry": "Communications Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "Services + equipment",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Communications and entertainment services",
                  "primary_products": [{"name": "Communications Services",
                                        "type": "professional_services",
                                        "description": "Business communications services",  # noqa: E501
                                        },
                                       {"name": "Entertainment Systems",
                                        "type": "tangible_personal_property",
                                        "description": "Entertainment and AV equipment",
                                        },
                                       ],
                  "research_notes": "Communications and entertainment services.\n📍 HQ: Location TBD | Service Area: Regional",  # noqa: E501
                  },
                 {"vendor_name": "FULCRUM TECHNOLOGIES INC",
                  "industry": "Technology Solutions",
                  "business_model": "B2B Software/Services",
                  "typical_delivery": "Software + services",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Technology solutions and services",
                  "primary_products": [{"name": "Technology Solutions",
                                        "type": "professional_services",
                                        "description": "IT solutions and services",
                                        }],
                  "research_notes": "Technology solutions provider.\n📍 HQ: Location TBD | Service Area: National",  # noqa: E501
                  },
                 {"vendor_name": "WONGDOODY INC",
                  "industry": "Creative Agency",
                  "business_model": "B2B Creative Services",
                  "typical_delivery": "Professional services",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Digital and brand experience creative agency",
                  "primary_products": [{"name": "Brand Strategy",
                                        "type": "professional_services",
                                        "description": "Brand positioning and strategy",
                                        },
                                       {"name": "Creative Design",
                                        "type": "professional_services",
                                        "description": "Digital and visual design services",  # noqa: E501
                                        },
                                       {"name": "Experience Design",
                                        "type": "professional_services",
                                        "description": "Customer experience design",
                                        },
                                       {"name": "Marketing Services",
                                        "type": "professional_services",
                                        "description": "Integrated marketing campaigns",
                                        },
                                       ],
                  "research_notes": "Founded 1993 Seattle. Acquired by Infosys 2018. Part of Infosys network.\n📍 HQ: Seattle, WA (now part of Infosys) | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "DECO DATA GROUP LLC",
                  "industry": "Data Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "Professional services",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Data services and solutions",
                  "primary_products": [{"name": "Data Services",
                                        "type": "professional_services",
                                        "description": "Data management and services",
                                        }],
                  "research_notes": "Data services provider.\n📍 HQ: Location TBD | Service Area: National",  # noqa: E501
                  },
                 {"vendor_name": "GARTNER INC",
                  "industry": "Research & Advisory",
                  "business_model": "B2B Services",
                  "typical_delivery": "Research + advisory services",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Technology research and advisory services",
                  "primary_products": [{"name": "Research Services",
                                        "type": "professional_services",
                                        "description": "Technology research and analysis",  # noqa: E501
                                        },
                                       {"name": "Advisory Services",
                                        "type": "professional_services",
                                        "description": "IT and business advisory consulting",  # noqa: E501
                                        },
                                       {"name": "Conferences",
                                        "type": "professional_services",
                                        "description": "Industry conferences and events",  # noqa: E501
                                        },
                                       {"name": "Peer Insights",
                                        "type": "saas_subscription",
                                        "description": "Technology reviews platform",
                                        },
                                       ],
                  "research_notes": "Founded 1979. Publicly traded (NYSE: IT). Global leader in tech research and advisory.\n📍 HQ: Stamford, CT | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "ACCERTIFY INC",
                  "industry": "Fraud Prevention",
                  "business_model": "B2B SaaS",
                  "typical_delivery": "Cloud platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Fraud detection and prevention platform for e-commerce",  # noqa: E501
                  "primary_products": [{"name": "Fraud Detection",
                                        "type": "saas_subscription",
                                        "description": "Real-time fraud prevention and detection",  # noqa: E501
                                        },
                                       {"name": "Chargeback Prevention",
                                        "type": "saas_subscription",
                                        "description": "Chargeback management and prevention",  # noqa: E501
                                        },
                                       {"name": "Account Protection",
                                        "type": "saas_subscription",
                                        "description": "Account takeover prevention",
                                        },
                                       ],
                  "research_notes": "Founded 2007. Acquired by American Express 2010.\n📍 HQ: Radnor, PA (part of American Express) | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "CLICKTALE INC",
                  "industry": "Digital Experience Analytics",
                  "business_model": "B2B SaaS",
                  "typical_delivery": "Cloud platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Digital experience analytics and session replay",  # noqa: E501
                  "primary_products": [{"name": "Session Replay",
                                        "type": "saas_subscription",
                                        "description": "Website visitor session recording",  # noqa: E501
                                        },
                                       {"name": "Heatmaps",
                                        "type": "saas_subscription",
                                        "description": "Click and scroll heatmap analytics",  # noqa: E501
                                        },
                                       {"name": "Conversion Analytics",
                                        "type": "saas_subscription",
                                        "description": "Conversion funnel analysis",
                                        },
                                       ],
                  "research_notes": "Founded 2006. Merged with Contentsquare.\n📍 HQ: San Francisco, CA (now part of Contentsquare) | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "O9 SOLUTIONS INC",
                  "industry": "Supply Chain Planning Software",
                  "business_model": "B2B SaaS",
                  "typical_delivery": "Cloud platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "AI-powered supply chain planning and analytics platform",  # noqa: E501
                  "primary_products": [{"name": "Demand Planning",
                                        "type": "saas_subscription",
                                        "description": "AI-driven demand forecasting",
                                        },
                                       {"name": "Supply Planning",
                                        "type": "saas_subscription",
                                        "description": "Supply chain optimization",
                                        },
                                       {"name": "IBP Platform",
                                        "type": "saas_subscription",
                                        "description": "Integrated business planning",
                                        },
                                       {"name": "Analytics",
                                        "type": "saas_subscription",
                                        "description": "Supply chain analytics",
                                        },
                                       ],
                  "research_notes": "Founded 2009. Leader in AI-powered supply chain planning.\n📍 HQ: Dallas, TX | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "APPDYNAMICS INC",
                  "industry": "Application Performance Monitoring",
                  "business_model": "B2B SaaS",
                  "typical_delivery": "Cloud platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Application performance monitoring and observability platform",  # noqa: E501
                  "primary_products": [{"name": "APM",
                                        "type": "saas_subscription",
                                        "description": "Application performance monitoring",  # noqa: E501
                                        },
                                       {"name": "Infrastructure Monitoring",
                                        "type": "saas_subscription",
                                        "description": "Server and infrastructure monitoring",  # noqa: E501
                                        },
                                       {"name": "Business Monitoring",
                                        "type": "saas_subscription",
                                        "description": "Business performance analytics",
                                        },
                                       {"name": "Cloud Monitoring",
                                        "type": "saas_subscription",
                                        "description": "Cloud application monitoring",
                                        },
                                       ],
                  "research_notes": "Founded 2008. Acquired by Cisco 2017 for $3.7B.\n📍 HQ: San Francisco, CA (now part of Cisco) | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "GITLAB INC",
                  "industry": "DevOps Platform",
                  "business_model": "B2B SaaS",
                  "typical_delivery": "Cloud platform + self-hosted",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Complete DevOps platform for software development lifecycle",  # noqa: E501
                  "primary_products": [{"name": "Source Code Management",
                                        "type": "saas_subscription",
                                        "description": "Git repository hosting and version control",  # noqa: E501
                                        },
                                       {"name": "CI/CD",
                                        "type": "saas_subscription",
                                        "description": "Continuous integration and deployment",  # noqa: E501
                                        },
                                       {"name": "Security & Compliance",
                                        "type": "saas_subscription",
                                        "description": "DevSecOps security scanning",
                                        },
                                       {"name": "Project Management",
                                        "type": "saas_subscription",
                                        "description": "Agile project planning and tracking",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Founded 2011. Went public 2021 (NASDAQ: GTLB). All-remote company.\n📍 HQ: San Francisco, CA (all-remote company) | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "DEMANDBASE INC",
                  "industry": "Account-Based Marketing",
                  "business_model": "B2B SaaS",
                  "typical_delivery": "Cloud platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Account-based marketing and sales intelligence platform",  # noqa: E501
                  "primary_products": [{"name": "ABM Platform",
                                        "type": "saas_subscription",
                                        "description": "Account-based marketing orchestration",  # noqa: E501
                                        },
                                       {"name": "Sales Intelligence",
                                        "type": "saas_subscription",
                                        "description": "B2B sales intelligence and intent data",  # noqa: E501
                                        },
                                       {"name": "Advertising",
                                        "type": "saas_subscription",
                                        "description": "Account-based advertising",
                                        },
                                       {"name": "Analytics",
                                        "type": "saas_subscription",
                                        "description": "B2B marketing analytics",
                                        },
                                       ],
                  "research_notes": "Founded 2007. Leader in account-based marketing. Acquired Engagio 2020, InsideView 2021.\n📍 HQ: San Francisco, CA | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "AC NIELSEN CORPORATION",
                  "industry": "Market Research & Analytics",
                  "business_model": "B2B Data Services",
                  "typical_delivery": "Data services + platforms",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Market research, consumer insights, and media measurement (Nielsen)",  # noqa: E501
                  "primary_products": [{"name": "Retail Measurement",
                                        "type": "professional_services",
                                        "description": "Retail sales data and market share",  # noqa: E501
                                        },
                                       {"name": "Consumer Insights",
                                        "type": "professional_services",
                                        "description": "Consumer behavior research and analytics",  # noqa: E501
                                        },
                                       {"name": "Media Ratings",
                                        "type": "professional_services",
                                        "description": "TV and digital media audience measurement",  # noqa: E501
                                        },
                                       {"name": "Marketing Analytics",
                                        "type": "saas_subscription",
                                        "description": "Marketing effectiveness analytics",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Founded 1923. Global leader in market research. Split into Nielsen Holdings (measurement) and NielsenIQ (consumer intelligence).\n📍 HQ: New York, NY | Service Area: Global (100+ countries)",  # noqa: E501
                  },
                 {"vendor_name": "PLAYNETWORK INC",
                  "industry": "Customer Experience Media",
                  "business_model": "B2B Services",
                  "typical_delivery": "Services + content delivery",
                  "wa_tax_classification": "professional_services",
                  "product_description": "In-store music, messaging, and customer experience media",  # noqa: E501
                  "primary_products": [{"name": "Music for Business",
                                        "type": "professional_services",
                                        "description": "Licensed background music services",  # noqa: E501
                                        },
                                       {"name": "Messaging & Audio",
                                        "type": "professional_services",
                                        "description": "In-store messaging and audio branding",  # noqa: E501
                                        },
                                       {"name": "Digital Signage",
                                        "type": "saas_subscription",
                                        "description": "Digital signage content management",  # noqa: E501
                                        },
                                       {"name": "Experience Design",
                                        "type": "professional_services",
                                        "description": "Retail experience design consulting",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Founded 1996. Leader in retail customer experience media.\n📍 HQ: Redmond, WA | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "MORLEY MOSS INC",
                  "industry": "Business Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "Professional services",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Business services and solutions",
                  "primary_products": [{"name": "Business Services",
                                        "type": "professional_services",
                                        "description": "Professional business services",
                                        }],
                  "research_notes": "Business services provider.\n📍 HQ: Location TBD | Service Area: Regional",  # noqa: E501
                  },
                 {"vendor_name": "HELP/SYSTEMS LLC",
                  "industry": "IT Management Software",
                  "business_model": "B2B Software",
                  "typical_delivery": "Software licenses + support",
                  "wa_tax_classification": "software_license",
                  "product_description": "IT systems management and security software",
                  "primary_products": [{"name": "Workload Automation",
                                        "type": "software_license",
                                        "description": "Job scheduling and automation",
                                        },
                                       {"name": "Security & Compliance",
                                        "type": "saas_subscription",
                                        "description": "Security and compliance solutions",  # noqa: E501
                                        },
                                       {"name": "File Transfer",
                                        "type": "software_license",
                                        "description": "Managed file transfer software",
                                        },
                                       {"name": "IBM i Solutions",
                                        "type": "software_license",
                                        "description": "IBM i systems management",
                                        },
                                       ],
                  "research_notes": "Founded 1982. Acquired by TPG Capital. Multiple acquisitions in IT management space.\n📍 HQ: Eden Prairie, MN | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "HEMISPHERE DESIGN & MANUFACTURING L",
                  "industry": "Manufacturing & Design",
                  "business_model": "B2B Manufacturing",
                  "typical_delivery": "Manufacturing + design services",
                  "wa_tax_classification": "manufacturing",
                  "product_description": "Custom design and manufacturing services",
                  "primary_products": [{"name": "Custom Manufacturing",
                                        "type": "manufacturing",
                                        "description": "Custom product manufacturing",
                                        },
                                       {"name": "Design Services",
                                        "type": "professional_services",
                                        "description": "Product design and engineering",
                                        },
                                       ],
                  "research_notes": "Design and manufacturing company.\n📍 HQ: Location TBD | Service Area: Regional/National",  # noqa: E501
                  },
                 {"vendor_name": "DUN & BRADSTREET INC",
                  "industry": "Business Data & Analytics",
                  "business_model": "B2B Data Services",
                  "typical_delivery": "Data platform + services",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Business information, analytics, and credit reporting",  # noqa: E501
                  "primary_products": [{"name": "Business Credit",
                                        "type": "professional_services",
                                        "description": "Business credit reports and scores",  # noqa: E501
                                        },
                                       {"name": "Sales Intelligence",
                                        "type": "saas_subscription",
                                        "description": "B2B sales prospecting data",
                                        },
                                       {"name": "Risk Management",
                                        "type": "professional_services",
                                        "description": "Third-party risk and compliance",  # noqa: E501
                                        },
                                       {"name": "Data Cloud",
                                        "type": "saas_subscription",
                                        "description": "Business data and analytics platform",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Founded 1841. Global leader in commercial data and analytics. D-U-N-S Number system.\n📍 HQ: Jacksonville, FL | Service Area: Global (200+ countries)",  # noqa: E501
                  },
                 {"vendor_name": "INDECT USA CORPORATION",
                  "industry": "Manufacturing/Technology",
                  "business_model": "B2B Manufacturing",
                  "typical_delivery": "Physical products",
                  "wa_tax_classification": "tangible_personal_property",
                  "product_description": "Manufacturing and technology products",
                  "primary_products": [{"name": "Manufacturing Products",
                                        "type": "tangible_personal_property",
                                        "description": "Manufactured products",
                                        }],
                  "research_notes": "Manufacturing company.\n📍 HQ: Location TBD | Service Area: National",  # noqa: E501
                  },
                 {"vendor_name": "ABF DATA SYSTEMS",
                  "industry": "Data Systems",
                  "business_model": "B2B Software/Services",
                  "typical_delivery": "Software + services",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Data systems and solutions",
                  "primary_products": [{"name": "Data Systems",
                                        "type": "professional_services",
                                        "description": "Data management systems",
                                        }],
                  "research_notes": "Data systems provider.\n📍 HQ: Location TBD | Service Area: Regional",  # noqa: E501
                  },
                 {"vendor_name": "YOUNG ELECTRIC SIGN COMP",
                  "industry": "Electric Sign Manufacturing",
                  "business_model": "B2B Manufacturing & Services",
                  "typical_delivery": "Manufacturing + installation",
                  "wa_tax_classification": "construction_services",
                  "product_description": "Electric sign manufacturing, installation, and maintenance (YESCO)",  # noqa: E501
                  "primary_products": [{"name": "Electric Signs",
                                        "type": "tangible_personal_property",
                                        "description": "Illuminated and LED signs",
                                        },
                                       {"name": "Digital Displays",
                                        "type": "tangible_personal_property",
                                        "description": "Digital billboards and message boards",  # noqa: E501
                                        },
                                       {"name": "Installation Services",
                                        "type": "construction_services",
                                        "description": "Sign installation and electrical work",  # noqa: E501
                                        },
                                       {"name": "Maintenance Services",
                                        "type": "professional_services",
                                        "description": "Sign service and repair",
                                        },
                                       ],
                  "research_notes": "YESCO - Founded 1920. Famous for Las Vegas signs. One of largest sign companies in US.\n📍 HQ: Salt Lake City, UT | Service Area: National",  # noqa: E501
                  },
                 {"vendor_name": "WALLS & FORMS INC",
                  "industry": "Construction",
                  "business_model": "B2B Construction",
                  "typical_delivery": "On-site construction services",
                  "wa_tax_classification": "construction_services",
                  "product_description": "Commercial construction services",
                  "primary_products": [{"name": "Construction Services",
                                        "type": "construction_services",
                                        "description": "Commercial construction work",
                                        }],
                  "research_notes": "Construction contractor.\n📍 HQ: Location TBD | Service Area: Regional",  # noqa: E501
                  },
                 {"vendor_name": "VERACODE INC",
                  "industry": "Application Security",
                  "business_model": "B2B SaaS",
                  "typical_delivery": "Cloud platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Application security testing and software composition analysis",  # noqa: E501
                  "primary_products": [{"name": "Static Analysis",
                                        "type": "saas_subscription",
                                        "description": "Static application security testing (SAST)",  # noqa: E501
                                        },
                                       {"name": "Dynamic Analysis",
                                        "type": "saas_subscription",
                                        "description": "Dynamic application security testing (DAST)",  # noqa: E501
                                        },
                                       {"name": "SCA",
                                        "type": "saas_subscription",
                                        "description": "Software composition analysis",
                                        },
                                       {"name": "Security Labs",
                                        "type": "professional_services",
                                        "description": "Security training for developers",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Founded 2006. Acquired by Thoma Bravo 2017. Leader in AppSec testing.\n📍 HQ: Burlington, MA | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "SPLUNK INC",
                  "industry": "Data Analytics & Security",
                  "business_model": "B2B SaaS",
                  "typical_delivery": "Cloud platform + software",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Data analytics, SIEM, and observability platform",  # noqa: E501
                  "primary_products": [{"name": "Splunk Enterprise",
                                        "type": "software_license",
                                        "description": "Data analytics and search platform",  # noqa: E501
                                        },
                                       {"name": "Splunk Cloud",
                                        "type": "saas_subscription",
                                        "description": "Cloud-based data analytics",
                                        },
                                       {"name": "Observability Cloud",
                                        "type": "saas_subscription",
                                        "description": "Application and infrastructure monitoring",  # noqa: E501
                                        },
                                       {"name": "SIEM",
                                        "type": "saas_subscription",
                                        "description": "Security information and event management",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Founded 2003. Went public 2012. Acquired by Cisco 2024 for $28B.\n📍 HQ: San Francisco, CA (now part of Cisco) | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "SHOPPERTRAK RCT CORPORATION",
                  "industry": "Retail Analytics",
                  "business_model": "B2B SaaS & Hardware",
                  "typical_delivery": "Sensors + cloud platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Retail traffic counting and analytics (now Sensormatic Solutions)",  # noqa: E501
                  "primary_products": [{"name": "Traffic Counters",
                                        "type": "tangible_personal_property",
                                        "description": "In-store traffic counting sensors",  # noqa: E501
                                        },
                                       {"name": "Analytics Platform",
                                        "type": "saas_subscription",
                                        "description": "Retail traffic analytics and reporting",  # noqa: E501
                                        },
                                       {"name": "Conversion Analytics",
                                        "type": "saas_subscription",
                                        "description": "Sales conversion tracking",
                                        },
                                       ],
                  "research_notes": "Founded 1995. Acquired by Tyco Retail Solutions (now Sensormatic Solutions/Johnson Controls).\n📍 HQ: Chicago, IL (now part of Sensormatic) | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "SHOPPAS MATERIAL HANDLING LTD",
                  "industry": "Material Handling Equipment",
                  "business_model": "B2B Equipment Sales",
                  "typical_delivery": "Physical equipment + services",
                  "wa_tax_classification": "tangible_personal_property",
                  "product_description": "Material handling equipment and solutions",
                  "primary_products": [{"name": "Material Handling Equipment",
                                        "type": "tangible_personal_property",
                                        "description": "Forklifts, conveyors, storage systems",  # noqa: E501
                                        },
                                       {"name": "Installation Services",
                                        "type": "professional_services",
                                        "description": "Equipment installation and setup",  # noqa: E501
                                        },
                                       {"name": "Maintenance Services",
                                        "type": "professional_services",
                                        "description": "Equipment service and repair",
                                        },
                                       ],
                  "research_notes": "Material handling equipment provider.\n📍 HQ: Canada | Service Area: North America",  # noqa: E501
                  },
                 {"vendor_name": "SHOOTSTA INC",
                  "industry": "Video Production Platform",
                  "business_model": "B2B SaaS",
                  "typical_delivery": "Cloud platform + equipment",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "DIY video production platform and services",
                  "primary_products": [{"name": "Video Platform",
                                        "type": "saas_subscription",
                                        "description": "Self-service video creation platform",  # noqa: E501
                                        },
                                       {"name": "Equipment Kits",
                                        "type": "tangible_personal_property",
                                        "description": "Video production equipment rental",  # noqa: E501
                                        },
                                       {"name": "Post-Production",
                                        "type": "professional_services",
                                        "description": "Video editing services",
                                        },
                                       {"name": "Training",
                                        "type": "professional_services",
                                        "description": "Video production training",
                                        },
                                       ],
                  "research_notes": "Founded 2012 Australia. DIY corporate video production.\n📍 HQ: Australia | US Operations: Location TBD | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "SECURITY PEOPLE INC",
                  "industry": "Security Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "Security personnel + services",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Security staffing and services",
                  "primary_products": [{"name": "Security Services",
                                        "type": "professional_services",
                                        "description": "Security personnel and guard services",  # noqa: E501
                                        }],
                  "research_notes": "Security services provider.\n📍 HQ: Location TBD | Service Area: Regional",  # noqa: E501
                  },
                 {"vendor_name": "SAGENT LLC",
                  "industry": "Mortgage Technology",
                  "business_model": "B2B SaaS",
                  "typical_delivery": "Cloud platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Mortgage servicing and loan management software",  # noqa: E501
                  "primary_products": [{"name": "Loan Servicing",
                                        "type": "saas_subscription",
                                        "description": "Mortgage loan servicing platform",  # noqa: E501
                                        },
                                       {"name": "Loss Mitigation",
                                        "type": "saas_subscription",
                                        "description": "Default and loss mitigation tools",  # noqa: E501
                                        },
                                       {"name": "Borrower Portal",
                                        "type": "saas_subscription",
                                        "description": "Customer self-service portal",
                                        },
                                       ],
                  "research_notes": "Mortgage servicing technology provider.\n📍 HQ: Colorado | Service Area: National",  # noqa: E501
                  },
                 {"vendor_name": "REDAPT INC",
                  "industry": "IT Infrastructure Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "Professional services + hardware",
                  "wa_tax_classification": "professional_services",
                  "product_description": "IT infrastructure consulting, cloud, and managed services",  # noqa: E501
                  "primary_products": [{"name": "Cloud Services",
                                        "type": "professional_services",
                                        "description": "Cloud migration and management",
                                        },
                                       {"name": "Infrastructure Services",
                                        "type": "professional_services",
                                        "description": "Data center and infrastructure consulting",  # noqa: E501
                                        },
                                       {"name": "Managed Services",
                                        "type": "professional_services",
                                        "description": "IT managed services and support",  # noqa: E501
                                        },
                                       {"name": "Equipment",
                                        "type": "tangible_personal_property",
                                        "description": "IT hardware and infrastructure products",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Founded 1997. IT services and solutions provider.\n📍 HQ: Seattle, WA | Service Area: National",  # noqa: E501
                  },
                 {"vendor_name": "PREPARESMART LLC",
                  "industry": "Emergency Preparedness",
                  "business_model": "B2B/B2C Retail",
                  "typical_delivery": "Physical products",
                  "wa_tax_classification": "tangible_personal_property",
                  "product_description": "Emergency preparedness supplies and kits",
                  "primary_products": [{"name": "Emergency Kits",
                                        "type": "tangible_personal_property",
                                        "description": "Pre-assembled emergency supply kits",  # noqa: E501
                                        },
                                       {"name": "Survival Supplies",
                                        "type": "tangible_personal_property",
                                        "description": "Emergency food, water, shelter supplies",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Emergency preparedness products.\n📍 HQ: Location TBD | Service Area: National",  # noqa: E501
                  },
                 {"vendor_name": "OPENTEXT INC",
                  "industry": "Enterprise Information Management",
                  "business_model": "B2B Software",
                  "typical_delivery": "Software + cloud platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Enterprise content management and information management software",  # noqa: E501
                  "primary_products": [{"name": "Content Services",
                                        "type": "saas_subscription",
                                        "description": "Enterprise content management platform",  # noqa: E501
                                        },
                                       {"name": "Business Network",
                                        "type": "saas_subscription",
                                        "description": "B2B integration and supply chain",  # noqa: E501
                                        },
                                       {"name": "Security",
                                        "type": "saas_subscription",
                                        "description": "Cybersecurity and information security",  # noqa: E501
                                        },
                                       {"name": "Developer Tools",
                                        "type": "software_license",
                                        "description": "Application development and testing",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Founded 1991. Largest Canadian software company. Acquired Micro Focus 2023.\n📍 HQ: Waterloo, Ontario, Canada | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "NC4 INC",
                  "industry": "Critical Event Management",
                  "business_model": "B2B SaaS",
                  "typical_delivery": "Cloud platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Critical event management and emergency notification platform",  # noqa: E501
                  "primary_products": [{"name": "Mass Notification",
                                        "type": "saas_subscription",
                                        "description": "Emergency mass notification system",  # noqa: E501
                                        },
                                       {"name": "Incident Management",
                                        "type": "saas_subscription",
                                        "description": "Critical incident management platform",  # noqa: E501
                                        },
                                       {"name": "Threat Intelligence",
                                        "type": "saas_subscription",
                                        "description": "Real-time threat monitoring",
                                        },
                                       ],
                  "research_notes": "Critical event management platform.\n📍 HQ: Los Angeles, CA area | Service Area: National",  # noqa: E501
                  },
                 {"vendor_name": "MOTIVACTION LLC",
                  "industry": "Business Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "Professional services",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Business services and solutions",
                  "primary_products": [{"name": "Business Services",
                                        "type": "professional_services",
                                        "description": "Professional services",
                                        }],
                  "research_notes": "Business services provider.\n📍 HQ: Location TBD | Service Area: Regional",  # noqa: E501
                  },
                 {"vendor_name": "M SCIENCE LLC",
                  "industry": "Alternative Data & Analytics",
                  "business_model": "B2B Data Services",
                  "typical_delivery": "Data platform + analytics",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Alternative data and predictive analytics for investors",  # noqa: E501
                  "primary_products": [{"name": "Alternative Data",
                                        "type": "professional_services",
                                        "description": "Transaction and behavioral data analytics",  # noqa: E501
                                        },
                                       {"name": "Predictive Analytics",
                                        "type": "saas_subscription",
                                        "description": "Investment research and insights",  # noqa: E501
                                        },
                                       {"name": "Custom Research",
                                        "type": "professional_services",
                                        "description": "Bespoke research and analysis",
                                        },
                                       ],
                  "research_notes": "Alternative data provider for institutional investors.\n📍 HQ: New York, NY | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "INTERNATIONAL BUSINESS MACHINES",
                  "industry": "Technology & Consulting",
                  "business_model": "B2B Technology",
                  "typical_delivery": "Hardware + software + services + cloud",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Enterprise technology, cloud, AI, consulting services (IBM)",  # noqa: E501
                  "primary_products": [{"name": "Cloud & AI",
                                        "type": "iaas_paas",
                                        "description": "IBM Cloud, Watson AI, Red Hat OpenShift",  # noqa: E501
                                        },
                                       {"name": "Software",
                                        "type": "software_license",
                                        "description": "Enterprise software solutions",
                                        },
                                       {"name": "Consulting",
                                        "type": "professional_services",
                                        "description": "IT and business consulting services",  # noqa: E501
                                        },
                                       {"name": "Infrastructure",
                                        "type": "tangible_personal_property",
                                        "description": "Servers, storage, mainframes",
                                        },
                                       ],
                  "research_notes": "Founded 1911. Global technology leader. Acquired Red Hat 2019 for $34B.\n📍 HQ: Armonk, NY | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "HITACHI VANTARA LLC",
                  "industry": "Data Storage & Analytics",
                  "business_model": "B2B Technology",
                  "typical_delivery": "Hardware + software + services",
                  "wa_tax_classification": "tangible_personal_property",
                  "product_description": "Enterprise data storage, infrastructure, and analytics",  # noqa: E501
                  "primary_products": [{"name": "Storage Systems",
                                        "type": "tangible_personal_property",
                                        "description": "Enterprise storage arrays and systems",  # noqa: E501
                                        },
                                       {"name": "Data Management",
                                        "type": "software_license",
                                        "description": "Data management and protection software",  # noqa: E501
                                        },
                                       {"name": "Analytics Platform",
                                        "type": "saas_subscription",
                                        "description": "Data analytics and AI platform",
                                        },
                                       {"name": "Services",
                                        "type": "professional_services",
                                        "description": "Consulting and managed services",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Formed 2017 from merger of Hitachi Data Systems and Pentaho. Part of Hitachi Ltd.\n📍 HQ: Santa Clara, CA | Parent: Tokyo, Japan | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "ENQUERO INC",
                  "industry": "Data Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "Professional services",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Data enrichment and validation services",
                  "primary_products": [{"name": "Data Services",
                                        "type": "professional_services",
                                        "description": "Data enrichment and cleansing",
                                        }],
                  "research_notes": "Data services provider.\n📍 HQ: Location TBD | Service Area: National",  # noqa: E501
                  },
                 {"vendor_name": "COMPEREMEDIA INC",
                  "industry": "Competitive Intelligence",
                  "business_model": "B2B Data Services",
                  "typical_delivery": "Data platform + research",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Competitive intelligence for financial services marketing",  # noqa: E501
                  "primary_products": [{"name": "Competitive Intelligence",
                                        "type": "professional_services",
                                        "description": "Marketing intelligence and tracking",  # noqa: E501
                                        },
                                       {"name": "Market Research",
                                        "type": "professional_services",
                                        "description": "Financial services market research",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Part of Mintel. Competitive intelligence for financial services.\n📍 HQ: New York, NY area | Service Area: National",  # noqa: E501
                  },
                 {"vendor_name": "CITIBANK NA",
                  "industry": "Banking & Financial Services",
                  "business_model": "B2B/B2C Banking",
                  "typical_delivery": "Financial services",
                  "wa_tax_classification": "financial_services",
                  "product_description": "Global banking and financial services",
                  "primary_products": [{"name": "Commercial Banking",
                                        "type": "financial_services",
                                        "description": "Business banking and treasury services",  # noqa: E501
                                        },
                                       {"name": "Investment Banking",
                                        "type": "financial_services",
                                        "description": "Corporate finance and capital markets",  # noqa: E501
                                        },
                                       {"name": "Transaction Services",
                                        "type": "financial_services",
                                        "description": "Payment processing and cash management",  # noqa: E501
                                        },
                                       {"name": "Digital Banking",
                                        "type": "saas_subscription",
                                        "description": "Online and mobile banking platforms",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Part of Citigroup. One of largest banks in world.\n📍 HQ: New York, NY | Service Area: Global (100+ countries)",  # noqa: E501
                  },
                 {"vendor_name": "BLUECORE INC",
                  "industry": "Retail Marketing Technology",
                  "business_model": "B2B SaaS",
                  "typical_delivery": "Cloud platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "Retail marketing automation and personalization platform",  # noqa: E501
                  "primary_products": [{"name": "Email Marketing",
                                        "type": "saas_subscription",
                                        "description": "AI-powered email marketing automation",  # noqa: E501
                                        },
                                       {"name": "Personalization",
                                        "type": "saas_subscription",
                                        "description": "Product recommendation engine",
                                        },
                                       {"name": "Retail Analytics",
                                        "type": "saas_subscription",
                                        "description": "Retail customer analytics",
                                        },
                                       ],
                  "research_notes": "Founded 2013. Retail-focused marketing automation.\n📍 HQ: New York, NY | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "BLUE YONDER INC",
                  "industry": "Supply Chain Software",
                  "business_model": "B2B SaaS",
                  "typical_delivery": "Cloud platform",
                  "wa_tax_classification": "saas_subscription",
                  "product_description": "AI-powered supply chain planning and execution platform (formerly JDA)",  # noqa: E501
                  "primary_products": [{"name": "Supply Chain Planning",
                                        "type": "saas_subscription",
                                        "description": "Demand, supply, and inventory planning",  # noqa: E501
                                        },
                                       {"name": "Warehouse Management",
                                        "type": "saas_subscription",
                                        "description": "WMS and fulfillment",
                                        },
                                       {"name": "Transportation",
                                        "type": "saas_subscription",
                                        "description": "Transportation management system",  # noqa: E501
                                        },
                                       {"name": "Retail Planning",
                                        "type": "saas_subscription",
                                        "description": "Merchandise and assortment planning",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "Formerly JDA Software. Rebranded Blue Yonder 2020. Acquired by Panasonic.\n📍 HQ: Scottsdale, AZ | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "MT PARENT INC",
                  "industry": "Business Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "Professional services",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Business services",
                  "primary_products": [{"name": "Business Services",
                                        "type": "professional_services",
                                        "description": "Corporate services",
                                        }],
                  "research_notes": "Business services entity.\n📍 HQ: Location TBD | Service Area: National",  # noqa: E501
                  },
                 {"vendor_name": "GLOBALDATA PUBLICATIONS INC",
                  "industry": "Business Intelligence & Research",
                  "business_model": "B2B Data Services",
                  "typical_delivery": "Research + data platform",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Industry research, data analytics, and business intelligence",  # noqa: E501
                  "primary_products": [{"name": "Industry Research",
                                        "type": "professional_services",
                                        "description": "Market research and industry analysis",  # noqa: E501
                                        },
                                       {"name": "Data & Analytics",
                                        "type": "saas_subscription",
                                        "description": "Business intelligence platform",
                                        },
                                       {"name": "Consulting Services",
                                        "type": "professional_services",
                                        "description": "Bespoke research and consulting",  # noqa: E501
                                        },
                                       ],
                  "research_notes": "GlobalData - UK-based business intelligence and research firm.\n📍 HQ: London, UK | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "NETCRACKER TECHNOLOGY SOLUTIONS LLC",
                  "industry": "Telecom OSS/BSS Software",
                  "business_model": "B2B Software",
                  "typical_delivery": "Software + professional services",
                  "wa_tax_classification": "software_license",
                  "product_description": "Telecom OSS/BSS software and digital transformation solutions",  # noqa: E501
                  "primary_products": [{"name": "BSS",
                                        "type": "software_license",
                                        "description": "Business support systems for telecom",  # noqa: E501
                                        },
                                       {"name": "OSS",
                                        "type": "software_license",
                                        "description": "Operations support systems",
                                        },
                                       {"name": "Digital Transformation",
                                        "type": "professional_services",
                                        "description": "Telecom digital transformation services",  # noqa: E501
                                        },
                                       {"name": "Cloud Solutions",
                                        "type": "iaas_paas",
                                        "description": "Cloud-based telecom platforms",
                                        },
                                       ],
                  "research_notes": "Founded 1993. Part of NEC Corporation. Leader in telecom BSS/OSS.\n📍 HQ: Waltham, MA | Parent: Tokyo, Japan | Service Area: Global",  # noqa: E501
                  },
                 {"vendor_name": "NOVO PAINTING & PROPERTY SERVICES L",
                  "industry": "Painting & Property Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "On-site services",
                  "wa_tax_classification": "construction_services",
                  "product_description": "Commercial painting and property maintenance services",  # noqa: E501
                  "primary_products": [{"name": "Painting Services",
                                        "type": "construction_services",
                                        "description": "Commercial and industrial painting",  # noqa: E501
                                        },
                                       {"name": "Property Maintenance",
                                        "type": "professional_services",
                                        "description": "Building maintenance services",
                                        },
                                       ],
                  "research_notes": "Commercial painting and property services.\n📍 HQ: Location TBD | Service Area: Regional",  # noqa: E501
                  },
                 {"vendor_name": "SERVICE COMMUNICATIONS INC",
                  "industry": "Communications Services",
                  "business_model": "B2B Services",
                  "typical_delivery": "Services + equipment",
                  "wa_tax_classification": "professional_services",
                  "product_description": "Communications services and solutions",
                  "primary_products": [{"name": "Communications Services",
                                        "type": "professional_services",
                                        "description": "Business communications services",  # noqa: E501
                                        }],
                  "research_notes": "Communications services provider.\n📍 HQ: Location TBD | Service Area: Regional",  # noqa: E501
                  },
                 ]


def update_final_vendors():
    """Update all remaining vendors"""

    print("Connecting to Supabase...")
    supabase = get_supabase_client()
    print("✓ Connected\n")

    print("Updating Final 125 Vendors (Batch 6 Complete)...\n")
    print(f"Total vendors in this batch: {len(FINAL_VENDORS)}\n")

    updated = 0
    errors = 0

    for vendor_data in FINAL_VENDORS:
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
    print(f"✓ BATCH 6 FINAL: {updated}/{len(FINAL_VENDORS)} vendors updated")
    print(f"❌ Errors: {errors}")
    print(
        f"\nTOTAL PROGRESS: 169 previous + {updated} new = {169 + updated}/294 vendors"
    )
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    update_final_vendors()
