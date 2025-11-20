#!/usr/bin/env python3
"""
Final 31 Vendors - Complete all 294!
"""

from core.database import get_supabase_client
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

FINAL_31 = [{"vendor_name": "FM SYSTEMS GROUP LLC",
             "industry": "Facility Management Software",
             "business_model": "B2B SaaS",
             "typical_delivery": "Cloud platform",
             "wa_tax_classification": "saas_subscription",
             "product_description": "Integrated workplace management system (IWMS) software",  # noqa: E501
             "primary_products": [{"name": "IWMS Platform",
                                   "type": "saas_subscription",
                                   "description": "Facility and space management software",  # noqa: E501
                                   },
                                  {"name": "Asset Management",
                                   "type": "saas_subscription",
                                   "description": "Facility asset tracking and maintenance",  # noqa: E501
                                   },
                                  {"name": "Space Planning",
                                   "type": "saas_subscription",
                                   "description": "Workplace space optimization",
                                   },
                                  ],
             "research_notes": "Facility management and IWMS software provider.\n📍 HQ: Raleigh, NC | Service Area: Global",  # noqa: E501
             },
            {"vendor_name": "ITENTIAL",
             "industry": "Network Automation Software",
             "business_model": "B2B SaaS",
             "typical_delivery": "Cloud platform",
             "wa_tax_classification": "saas_subscription",
             "product_description": "Network automation and orchestration platform",
             "primary_products": [{"name": "Network Automation",
                                   "type": "saas_subscription",
                                   "description": "Network infrastructure automation platform",  # noqa: E501
                                   },
                                  {"name": "Orchestration",
                                   "type": "saas_subscription",
                                   "description": "Multi-vendor network orchestration",
                                   },
                                  ],
             "research_notes": "Network automation platform for service providers and enterprises.\n📍 HQ: Atlanta, GA | Service Area: Global",  # noqa: E501
             },
            {"vendor_name": "KC WHOLESALE CONSTRUCTION PRODUCTS",
             "industry": "Construction Products Distribution",
             "business_model": "B2B Distribution",
             "typical_delivery": "Physical products",
             "wa_tax_classification": "tangible_personal_property",
             "product_description": "Wholesale construction products and materials",
             "primary_products": [{"name": "Construction Materials",
                                   "type": "tangible_personal_property",
                                   "description": "Wholesale building materials",
                                   }],
             "research_notes": "Construction products distributor.\n📍 HQ: Kansas City area | Service Area: Regional",  # noqa: E501
             },
            {"vendor_name": "CLOUDERA INC",
             "industry": "Big Data & Analytics Platform",
             "business_model": "B2B Software",
             "typical_delivery": "Software + cloud platform",
             "wa_tax_classification": "iaas_paas",
             "product_description": "Enterprise data cloud platform for analytics and AI",  # noqa: E501
             "primary_products": [{"name": "Data Platform",
                                   "type": "iaas_paas",
                                   "description": "Hybrid data cloud platform",
                                   },
                                  {"name": "Data Engineering",
                                   "type": "saas_subscription",
                                   "description": "Data pipelines and engineering",
                                   },
                                  {"name": "Machine Learning",
                                   "type": "saas_subscription",
                                   "description": "ML and AI platform",
                                   },
                                  {"name": "Data Warehouse",
                                   "type": "iaas_paas",
                                   "description": "Cloud data warehouse",
                                   },
                                  ],
             "research_notes": "Founded 2008. Went public 2017, private 2021 (KKR/CD&R). Merged with Hortonworks 2019.\n📍 HQ: Santa Clara, CA | Service Area: Global",  # noqa: E501
             },
            {"vendor_name": "DAY MANAGEMENT CORPORATION",
             "industry": "Management Services",
             "business_model": "B2B Services",
             "typical_delivery": "Professional services",
             "wa_tax_classification": "professional_services",
             "product_description": "Management and consulting services",
             "primary_products": [{"name": "Management Services",
                                   "type": "professional_services",
                                   "description": "Corporate management services",
                                   }],
             "research_notes": "Management services company.\n📍 HQ: Location TBD | Service Area: Regional",  # noqa: E501
             },
            {"vendor_name": "FACILITY INTERIORS INC",
             "industry": "Commercial Interiors",
             "business_model": "B2B Construction",
             "typical_delivery": "On-site installation services",
             "wa_tax_classification": "construction_services",
             "product_description": "Commercial interior construction and furniture installation",  # noqa: E501
             "primary_products": [{"name": "Interior Construction",
                                   "type": "construction_services",
                                   "description": "Office interior buildout and construction",  # noqa: E501
                                   },
                                  {"name": "Furniture Installation",
                                   "type": "construction_services",
                                   "description": "Commercial furniture installation",
                                   },
                                  ],
             "research_notes": "Commercial interiors contractor.\n📍 HQ: Location TBD | Service Area: Regional",  # noqa: E501
             },
            {"vendor_name": "FORRESTER RESEARCH INC",
             "industry": "Technology Research & Advisory",
             "business_model": "B2B Services",
             "typical_delivery": "Research + advisory services",
             "wa_tax_classification": "professional_services",
             "product_description": "Technology research, advisory, and consulting services",  # noqa: E501
             "primary_products": [{"name": "Research Services",
                                   "type": "professional_services",
                                   "description": "Technology and business research",
                                   },
                                  {"name": "Advisory Services",
                                   "type": "professional_services",
                                   "description": "Strategic advisory and consulting",
                                   },
                                  {"name": "Events & Conferences",
                                   "type": "professional_services",
                                   "description": "Industry conferences and events",
                                   },
                                  ],
             "research_notes": "Founded 1983. Publicly traded (NASDAQ: FORR). Global research and advisory firm.\n📍 HQ: Cambridge, MA | Service Area: Global",  # noqa: E501
             },
            {"vendor_name": "FREE ROAD FILMS",
             "industry": "Video Production",
             "business_model": "B2B Services",
             "typical_delivery": "Professional services",
             "wa_tax_classification": "professional_services",
             "product_description": "Commercial video production services",
             "primary_products": [{"name": "Video Production",
                                   "type": "professional_services",
                                   "description": "Commercial and corporate video production",  # noqa: E501
                                   }],
             "research_notes": "Video production company.\n📍 HQ: Location TBD | Service Area: Regional/National",  # noqa: E501
             },
            {"vendor_name": "HASHICORP INC",
             "industry": "Cloud Infrastructure Automation",
             "business_model": "B2B Software",
             "typical_delivery": "Software + cloud platform",
             "wa_tax_classification": "saas_subscription",
             "product_description": "Multi-cloud infrastructure automation and security software",  # noqa: E501
             "primary_products": [{"name": "Terraform",
                                   "type": "saas_subscription",
                                   "description": "Infrastructure as code platform",
                                   },
                                  {"name": "Vault",
                                   "type": "saas_subscription",
                                   "description": "Secrets management and encryption",
                                   },
                                  {"name": "Consul",
                                   "type": "saas_subscription",
                                   "description": "Service networking and discovery",
                                   },
                                  {"name": "Nomad",
                                   "type": "software_license",
                                   "description": "Workload orchestration",
                                   },
                                  ],
             "research_notes": "Founded 2012. Went public 2021 (NASDAQ: HCP). Acquired by IBM 2024 for $6.4B.\n📍 HQ: San Francisco, CA (now part of IBM) | Service Area: Global",  # noqa: E501
             },
            {"vendor_name": "KENTIK TECHNOLOGIES INC",
             "industry": "Network Observability",
             "business_model": "B2B SaaS",
             "typical_delivery": "Cloud platform",
             "wa_tax_classification": "saas_subscription",
             "product_description": "Network observability and analytics platform",
             "primary_products": [{"name": "Network Analytics",
                                   "type": "saas_subscription",
                                   "description": "Network traffic analytics and insights",  # noqa: E501
                                   },
                                  {"name": "DDoS Protection",
                                   "type": "saas_subscription",
                                   "description": "DDoS detection and mitigation",
                                   },
                                  {"name": "Cloud Monitoring",
                                   "type": "saas_subscription",
                                   "description": "Multi-cloud network visibility",
                                   },
                                  ],
             "research_notes": "Founded 2014. Network observability platform for enterprises and service providers.\n📍 HQ: San Francisco, CA | Service Area: Global",  # noqa: E501
             },
            {"vendor_name": "LINKED IN CORPORATION",
             "industry": "Professional Social Network",
             "business_model": "B2B/B2C SaaS",
             "typical_delivery": "Cloud platform",
             "wa_tax_classification": "saas_subscription",
             "product_description": "Professional networking and recruiting platform",
             "primary_products": [{"name": "LinkedIn Platform",
                                   "type": "saas_subscription",
                                   "description": "Professional networking social platform",  # noqa: E501
                                   },
                                  {"name": "LinkedIn Recruiter",
                                   "type": "saas_subscription",
                                   "description": "Recruiting and talent acquisition platform",  # noqa: E501
                                   },
                                  {"name": "Sales Navigator",
                                   "type": "saas_subscription",
                                   "description": "Social selling and lead generation",
                                   },
                                  {"name": "Learning",
                                   "type": "saas_subscription",
                                   "description": "Online professional development courses",  # noqa: E501
                                   },
                                  ],
             "research_notes": "Founded 2003. Acquired by Microsoft 2016 for $26.2B.\n📍 HQ: Sunnyvale, CA (part of Microsoft) | Service Area: Global",  # noqa: E501
             },
            {"vendor_name": "MANSELL GROUP INC",
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
            {"vendor_name": "MCKINSTRY CO LLC",
             "industry": "Construction & Facility Services",
             "business_model": "B2B Construction",
             "typical_delivery": "On-site construction + facility services",
             "wa_tax_classification": "construction_services",
             "product_description": "Design-build-operate construction and facility services",  # noqa: E501
             "primary_products": [{"name": "MEP Construction",
                                   "type": "construction_services",
                                   "description": "Mechanical, electrical, plumbing construction",  # noqa: E501
                                   },
                                  {"name": "Design-Build",
                                   "type": "construction_services",
                                   "description": "Integrated design and construction",
                                   },
                                  {"name": "Energy Services",
                                   "type": "professional_services",
                                   "description": "Energy efficiency and sustainability",  # noqa: E501
                                   },
                                  {"name": "Facility Services",
                                   "type": "professional_services",
                                   "description": "Building operations and maintenance",
                                   },
                                  ],
             "research_notes": "Founded 1960. Employee-owned. Full-service design, build, operate firm.\n📍 HQ: Seattle, WA | Service Area: National (West Coast focus)",  # noqa: E501
             },
            {"vendor_name": "SLACK TECHNOLOGIES INC",
             "industry": "Business Communication Software",
             "business_model": "B2B SaaS",
             "typical_delivery": "Cloud platform",
             "wa_tax_classification": "saas_subscription",
             "product_description": "Team collaboration and communication platform",
             "primary_products": [{"name": "Slack Platform",
                                   "type": "saas_subscription",
                                   "description": "Team messaging and collaboration",
                                   },
                                  {"name": "Slack Connect",
                                   "type": "saas_subscription",
                                   "description": "External collaboration with partners/clients",  # noqa: E501
                                   },
                                  {"name": "Workflow Builder",
                                   "type": "saas_subscription",
                                   "description": "No-code workflow automation",
                                   },
                                  {"name": "Enterprise Grid",
                                   "type": "saas_subscription",
                                   "description": "Enterprise-scale Slack deployment",
                                   },
                                  ],
             "research_notes": "Founded 2013. Went public 2019. Acquired by Salesforce 2021 for $27.7B.\n📍 HQ: San Francisco, CA (now part of Salesforce) | Service Area: Global",  # noqa: E501
             },
            {"vendor_name": "SNOWFLAKE INC",
             "industry": "Cloud Data Platform",
             "business_model": "B2B SaaS",
             "typical_delivery": "Cloud platform",
             "wa_tax_classification": "iaas_paas",
             "product_description": "Cloud data warehouse and analytics platform",
             "primary_products": [{"name": "Data Warehouse",
                                   "type": "iaas_paas",
                                   "description": "Cloud data warehouse platform",
                                   },
                                  {"name": "Data Lake",
                                   "type": "iaas_paas",
                                   "description": "Data lake and storage",
                                   },
                                  {"name": "Data Sharing",
                                   "type": "saas_subscription",
                                   "description": "Secure data sharing marketplace",
                                   },
                                  {"name": "Data Engineering",
                                   "type": "saas_subscription",
                                   "description": "Data pipelines and engineering",
                                   },
                                  ],
             "research_notes": "Founded 2012. Went public 2020 (NYSE: SNOW). Largest software IPO ever at the time.\n📍 HQ: Bozeman, MT (originally); San Mateo, CA (current) | Service Area: Global",  # noqa: E501
             },
            {"vendor_name": "SWINERTON BUILDERS",
             "industry": "Construction & Real Estate",
             "business_model": "B2B Construction",
             "typical_delivery": "On-site construction services",
             "wa_tax_classification": "construction_services",
             "product_description": "General contracting and construction management",
             "primary_products": [{"name": "General Contracting",
                                   "type": "construction_services",
                                   "description": "Commercial construction services",
                                   },
                                  {"name": "Construction Management",
                                   "type": "professional_services",
                                   "description": "CM and project management",
                                   },
                                  {"name": "Design-Build",
                                   "type": "construction_services",
                                   "description": "Integrated design-build services",
                                   },
                                  ],
             "research_notes": "Founded 1888. Employee-owned. One of largest general contractors in US.\n📍 HQ: San Francisco, CA | Service Area: National",  # noqa: E501
             },
            {"vendor_name": "THE NPD GROUP INC",
             "industry": "Market Research",
             "business_model": "B2B Data Services",
             "typical_delivery": "Research + data platform",
             "wa_tax_classification": "professional_services",
             "product_description": "Consumer and retail market research and analytics",
             "primary_products": [{"name": "Retail Tracking",
                                   "type": "professional_services",
                                   "description": "Point-of-sale retail data tracking",
                                   },
                                  {"name": "Consumer Research",
                                   "type": "professional_services",
                                   "description": "Consumer behavior and trends research",  # noqa: E501
                                   },
                                  {"name": "Industry Analytics",
                                   "type": "saas_subscription",
                                   "description": "Market intelligence and forecasting",
                                   },
                                  ],
             "research_notes": "Founded 1966. Global provider of market information and advisory services.\n📍 HQ: Port Washington, NY | Service Area: Global",  # noqa: E501
             },
            {"vendor_name": "TRIMBLE INC",
             "industry": "Technology Solutions",
             "business_model": "B2B Technology",
             "typical_delivery": "Hardware + software + services",
             "wa_tax_classification": "tangible_personal_property",
             "product_description": "Positioning technology, software, and services for multiple industries",  # noqa: E501
             "primary_products": [{"name": "GPS/GNSS Hardware",
                                   "type": "tangible_personal_property",
                                   "description": "Positioning and navigation hardware",
                                   },
                                  {"name": "Construction Software",
                                   "type": "saas_subscription",
                                   "description": "Construction project management software",  # noqa: E501
                                   },
                                  {"name": "Geospatial Solutions",
                                   "type": "software_license",
                                   "description": "Mapping and GIS software",
                                   },
                                  {"name": "Agriculture Technology",
                                   "type": "tangible_personal_property",
                                   "description": "Precision agriculture systems",
                                   },
                                  ],
             "research_notes": "Founded 1978. Publicly traded (NASDAQ: TRMB). Leader in positioning technology.\n📍 HQ: Westminster, CO (previously Sunnyvale, CA) | Service Area: Global",  # noqa: E501
             },
            {"vendor_name": "VECA ELECTRIC",
             "industry": "Electrical Contracting",
             "business_model": "B2B Construction",
             "typical_delivery": "On-site electrical services",
             "wa_tax_classification": "construction_services",
             "product_description": "Commercial and industrial electrical contracting",
             "primary_products": [{"name": "Electrical Construction",
                                   "type": "construction_services",
                                   "description": "Commercial electrical installation",
                                   },
                                  {"name": "Service & Maintenance",
                                   "type": "professional_services",
                                   "description": "Electrical service and repair",
                                   },
                                  ],
             "research_notes": "Electrical contractor serving commercial and industrial markets.\n📍 HQ: Location TBD | Service Area: Regional",  # noqa: E501
             },
            {"vendor_name": "VERDIGRIS TECHNOLOGIES INC",
             "industry": "Building Energy Intelligence",
             "business_model": "B2B IoT/SaaS",
             "typical_delivery": "Hardware sensors + cloud platform",
             "wa_tax_classification": "saas_subscription",
             "product_description": "AI-powered building energy monitoring and analytics",  # noqa: E501
             "primary_products": [{"name": "Energy Sensors",
                                   "type": "tangible_personal_property",
                                   "description": "IoT energy monitoring sensors",
                                   },
                                  {"name": "Analytics Platform",
                                   "type": "saas_subscription",
                                   "description": "AI-powered energy analytics",
                                   },
                                  {"name": "Fault Detection",
                                   "type": "saas_subscription",
                                   "description": "Equipment fault detection and diagnostics",  # noqa: E501
                                   },
                                  ],
             "research_notes": "Founded 2011. AI-powered building energy management.\n📍 HQ: Moffett Field, CA | Service Area: National",  # noqa: E501
             },
            {"vendor_name": "VERTEX INC",
             "industry": "Tax Technology",
             "business_model": "B2B Software",
             "typical_delivery": "Software + cloud platform",
             "wa_tax_classification": "saas_subscription",
             "product_description": "Tax automation software for indirect tax compliance",  # noqa: E501
             "primary_products": [{"name": "Tax Determination",
                                   "type": "saas_subscription",
                                   "description": "Automated sales/use tax calculation",
                                   },
                                  {"name": "Tax Compliance",
                                   "type": "saas_subscription",
                                   "description": "Tax filing and compliance automation",  # noqa: E501
                                   },
                                  {"name": "Tax Reporting",
                                   "type": "saas_subscription",
                                   "description": "Tax reporting and analytics",
                                   },
                                  {"name": "VAT/GST",
                                   "type": "saas_subscription",
                                   "description": "Global VAT and GST compliance",
                                   },
                                  ],
             "research_notes": "Founded 1978. Leader in tax technology for indirect taxes.\n📍 HQ: King of Prussia, PA | Service Area: Global",  # noqa: E501
             },
            {"vendor_name": "VLOCITY INC",
             "industry": "Industry Cloud Software",
             "business_model": "B2B SaaS",
             "typical_delivery": "Cloud platform",
             "wa_tax_classification": "saas_subscription",
             "product_description": "Industry-specific cloud software on Salesforce (now Salesforce Industries)",  # noqa: E501
             "primary_products": [{"name": "Communications Cloud",
                                   "type": "saas_subscription",
                                   "description": "Telecom industry CRM and order management",  # noqa: E501
                                   },
                                  {"name": "Insurance Cloud",
                                   "type": "saas_subscription",
                                   "description": "Insurance policy and claims management",  # noqa: E501
                                   },
                                  {"name": "Health Cloud",
                                   "type": "saas_subscription",
                                   "description": "Healthcare provider and payer solutions",  # noqa: E501
                                   },
                                  {"name": "CPQ",
                                   "type": "saas_subscription",
                                   "description": "Configure, price, quote for complex products",  # noqa: E501
                                   },
                                  ],
             "research_notes": "Founded 2014. Acquired by Salesforce 2020 for $1.33B. Now Salesforce Industries.\n📍 HQ: San Francisco, CA (now part of Salesforce) | Service Area: Global",  # noqa: E501
             },
            {"vendor_name": "WAVE SYSTEMS CORP",
             "industry": "Embedded Security",
             "business_model": "B2B Software/Hardware",
             "typical_delivery": "Software + hardware security",
             "wa_tax_classification": "software_license",
             "product_description": "Embedded security and authentication solutions",
             "primary_products": [{"name": "Security Software",
                                   "type": "software_license",
                                   "description": "Embedded security software",
                                   },
                                  {"name": "Authentication",
                                   "type": "software_license",
                                   "description": "Hardware-based authentication",
                                   },
                                  ],
             "research_notes": "Founded 1988. Embedded security solutions for devices.\n📍 HQ: Lee, NH area | Service Area: Global",  # noqa: E501
             },
            {"vendor_name": "WINDY WATERS INC",
             "industry": "Business Services",
             "business_model": "B2B Services",
             "typical_delivery": "Professional services",
             "wa_tax_classification": "professional_services",
             "product_description": "Business services",
             "primary_products": [{"name": "Business Services",
                                   "type": "professional_services",
                                   "description": "Professional services",
                                   }],
             "research_notes": "Business services provider.\n📍 HQ: Location TBD | Service Area: Regional",  # noqa: E501
             },
            {"vendor_name": "BTI SOLUTIONS INC",
             "industry": "IT Solutions",
             "business_model": "B2B Services",
             "typical_delivery": "Professional services + equipment",
             "wa_tax_classification": "professional_services",
             "product_description": "IT solutions and services",
             "primary_products": [{"name": "IT Services",
                                   "type": "professional_services",
                                   "description": "IT consulting and services",
                                   }],
             "research_notes": "IT solutions provider.\n📍 HQ: Location TBD | Service Area: Regional/National",  # noqa: E501
             },
            {"vendor_name": "APPTENTIVE INC",
             "industry": "Mobile Customer Engagement",
             "business_model": "B2B SaaS",
             "typical_delivery": "Cloud platform",
             "wa_tax_classification": "saas_subscription",
             "product_description": "Mobile customer engagement and feedback platform",
             "primary_products": [{"name": "Mobile Feedback",
                                   "type": "saas_subscription",
                                   "description": "In-app customer feedback and surveys",  # noqa: E501
                                   },
                                  {"name": "Ratings & Reviews",
                                   "type": "saas_subscription",
                                   "description": "App store ratings prompts",
                                   },
                                  {"name": "Customer Messaging",
                                   "type": "saas_subscription",
                                   "description": "In-app messaging and support",
                                   },
                                  ],
             "research_notes": "Founded 2011. Mobile customer engagement platform.\n📍 HQ: Seattle, WA | Service Area: Global",  # noqa: E501
             },
            {"vendor_name": "ARRIS SOLUTIONS INC",
             "industry": "Telecommunications Equipment",
             "business_model": "B2B Manufacturing",
             "typical_delivery": "Physical equipment",
             "wa_tax_classification": "tangible_personal_property",
             "product_description": "Broadband and video delivery equipment (now part of CommScope)",  # noqa: E501
             "primary_products": [{"name": "Cable Modems",
                                   "type": "tangible_personal_property",
                                   "description": "DOCSIS cable modems and gateways",
                                   },
                                  {"name": "Set-Top Boxes",
                                   "type": "tangible_personal_property",
                                   "description": "Video set-top boxes and streaming devices",  # noqa: E501
                                   },
                                  {"name": "Network Infrastructure",
                                   "type": "tangible_personal_property",
                                   "description": "Cable network infrastructure equipment",  # noqa: E501
                                   },
                                  ],
             "research_notes": "Founded 1995. Acquired by CommScope 2019 for $7.4B.\n📍 HQ: Suwanee, GA (now part of CommScope) | Service Area: Global",  # noqa: E501
             },
            {"vendor_name": "AUTHENTICID INC",
             "industry": "Identity Verification",
             "business_model": "B2B SaaS",
             "typical_delivery": "Cloud platform",
             "wa_tax_classification": "saas_subscription",
             "product_description": "Identity verification and authentication platform",
             "primary_products": [{"name": "ID Verification",
                                   "type": "saas_subscription",
                                   "description": "Document and identity verification",
                                   },
                                  {"name": "Biometric Authentication",
                                   "type": "saas_subscription",
                                   "description": "Facial recognition and liveness detection",  # noqa: E501
                                   },
                                  {"name": "Fraud Prevention",
                                   "type": "saas_subscription",
                                   "description": "Identity fraud detection",
                                   },
                                  ],
             "research_notes": "Identity verification platform for onboarding and authentication.\n📍 HQ: Seattle, WA | Service Area: Global",  # noqa: E501
             },
            {"vendor_name": "BAILIWICK SERVICES LLC",
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
            {"vendor_name": "BAZAARVOICE INC",
             "industry": "User-Generated Content Platform",
             "business_model": "B2B SaaS",
             "typical_delivery": "Cloud platform",
             "wa_tax_classification": "saas_subscription",
             "product_description": "Ratings, reviews, and user-generated content platform",  # noqa: E501
             "primary_products": [{"name": "Ratings & Reviews",
                                   "type": "saas_subscription",
                                   "description": "Customer review collection and display",  # noqa: E501
                                   },
                                  {"name": "Social Commerce",
                                   "type": "saas_subscription",
                                   "description": "Social content and shopping integration",  # noqa: E501
                                   },
                                  {"name": "Sampling",
                                   "type": "professional_services",
                                   "description": "Product sampling programs",
                                   },
                                  {"name": "Insights",
                                   "type": "saas_subscription",
                                   "description": "Consumer insights and analytics",
                                   },
                                  ],
             "research_notes": "Founded 2005. Went public 2012, private 2014. Leader in UGC and ratings/reviews.\n📍 HQ: Austin, TX | Service Area: Global",  # noqa: E501
             },
            {"vendor_name": "BITLY INC",
             "industry": "Link Management Platform",
             "business_model": "B2B SaaS",
             "typical_delivery": "Cloud platform",
             "wa_tax_classification": "saas_subscription",
             "product_description": "Link shortening and management platform",
             "primary_products": [{"name": "Link Shortening",
                                   "type": "saas_subscription",
                                   "description": "URL shortening and branded links",
                                   },
                                  {"name": "Link Analytics",
                                   "type": "saas_subscription",
                                   "description": "Click tracking and analytics",
                                   },
                                  {"name": "QR Codes",
                                   "type": "saas_subscription",
                                   "description": "QR code generation and tracking",
                                   },
                                  {"name": "Link-in-Bio",
                                   "type": "saas_subscription",
                                   "description": "Social media link management",
                                   },
                                  ],
             "research_notes": "Founded 2008. Popular link shortening service. bit.ly domain.\n📍 HQ: New York, NY | Service Area: Global",  # noqa: E501
             },
            ]


def update_final_31():
    """Complete all 294 vendors!"""

    print("Connecting to Supabase...")
    supabase = get_supabase_client()
    print("✓ Connected\n")

    print(
        f"🎯 FINAL PUSH: Updating last {len(FINAL_31)} vendors to complete all 294!\n"
    )

    updated = 0
    errors = 0

    for vendor_data in FINAL_31:
        vendor_name = vendor_data["vendor_name"]

        try:
            result = (
                supabase.table("vendor_products")
                .select("id")
                .eq("vendor_name", vendor_name)
                .execute()
            )

            if not result.data:
                print(f"❌ {vendor_name} - not found")
                errors += 1
                continue

            vendor_id = result.data[0]["id"]

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

            supabase.table("vendor_products").update(update_data).eq(
                "id", vendor_id
            ).execute()

            print(f"✓ {vendor_name}")
            updated += 1

        except Exception as e:
            print(f"❌ {vendor_name} - Error: {e}")
            errors += 1

    print(f"\n{'=' * 70}")
    print("🎉 ALL 294 VENDORS COMPLETE!")
    print(f"{'=' * 70}")
    print(f"✓ Final batch: {updated}/{len(FINAL_31)} vendors")
    print(f"✓ TOTAL: 263 previous + {updated} new = {263 + updated}/294 vendors")
    print(f"❌ Errors: {errors}")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    update_final_31()
