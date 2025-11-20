#!/usr/bin/env python3
"""
Update Supabase with Batch 3 researched vendor data (vendors 41-65)
"""

from core.database import get_supabase_client
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Batch 3: Researched vendor data (vendors 41-65)
BATCH3_VENDORS = [{"vendor_name": "MICROSOFT CORPORATION",
                   "industry": "Technology & Cloud Services",
                   "business_model": "B2B/B2C Software & Cloud",
                   "typical_delivery": "Cloud-based SaaS + software licenses",
                   "wa_tax_classification": "digital_automated_service",
                   "product_description": "Cloud computing, productivity software, business applications - Azure, Microsoft 365, Dynamics",  # noqa: E501
                   "primary_products": [{"name": "Microsoft 365",
                                         "type": "saas_subscription",
                                         "description": "Cloud productivity suite: Office apps, OneDrive, Teams, SharePoint",  # noqa: E501
                                         },
                                        {"name": "Microsoft Azure",
                                         "type": "iaas_paas",
                                         "description": "Cloud computing platform: IaaS, PaaS, SaaS services",  # noqa: E501
                                         },
                                        {"name": "Dynamics 365",
                                         "type": "saas_subscription",
                                         "description": "Cloud ERP and CRM solutions",
                                         },
                                        {"name": "Windows",
                                         "type": "software_license",
                                         "description": "Operating system software licenses",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Fortune 500 #14. $211B revenue. Redmond, WA. Azure Active Directory integrates with O365. Mix of SaaS subscriptions and software licenses.",  # noqa: E501
                   },
                  {"vendor_name": "GIGAMON INC",
                   "industry": "Network Visibility & Security",
                   "business_model": "B2B SaaS + Hardware",
                   "typical_delivery": "Network appliances + cloud platform",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Network visibility and security solutions - deep observability pipeline, traffic analysis",  # noqa: E501
                   "primary_products": [{"name": "Deep Observability Pipeline",
                                         "type": "saas_subscription",
                                         "description": "Network intelligence delivery to security/observability tools",  # noqa: E501
                                         },
                                        {"name": "GigaVUE Appliances",
                                         "type": "tangible_personal_property",
                                         "description": "Physical network visibility hardware",  # noqa: E501
                                         },
                                        {"name": "GigaVUE Cloud Suite",
                                         "type": "saas_subscription",
                                         "description": "Cloud-based visibility and monitoring",  # noqa: E501
                                         },
                                        {"name": "Precryption Technology",
                                         "type": "software_license",
                                         "description": "TLS 1.3 encrypted traffic visibility",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 2004. Santa Clara, CA. Privately held (Elliott Management). 4,000+ customers. Makes tools 90% more efficient.",  # noqa: E501
                   },
                  {"vendor_name": "AUTOMATED SYSTEMS DESIGN INC",
                   "industry": "Industrial Automation",
                   "business_model": "B2B Services",
                   "typical_delivery": "Engineering services + on-site installation",
                   "wa_tax_classification": "professional_services",
                   "product_description": "Industrial automation systems - robotics, control systems, foundry automation (tentative)",  # noqa: E501
                   "primary_products": [{"name": "Robotic Systems",
                                         "type": "professional_services",
                                         "description": "Industrial automation design and engineering",  # noqa: E501
                                         },
                                        {"name": "Control Systems",
                                         "type": "professional_services",
                                         "description": "Controller design and programming",  # noqa: E501
                                         },
                                        {"name": "Foundry Automation",
                                         "type": "professional_services",
                                         "description": "Aluminum foundry automation systems",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "TENTATIVE - Multiple companies with similar names found. Dayton OH location specializes in foundry robotics. Needs verification.",  # noqa: E501
                   },
                  {"vendor_name": "ROYAL MECHANICAL SERVICES INC",
                   "industry": "HVAC & Mechanical Services",
                   "business_model": "B2B Services",
                   "typical_delivery": "On-site mechanical services",
                   "wa_tax_classification": "construction_services",
                   "product_description": "HVAC mechanical contracting - installation, service, maintenance, sheet metal, plumbing",  # noqa: E501
                   "primary_products": [{"name": "HVAC Installation",
                                         "type": "construction_services",
                                         "description": "Commercial HVAC system installation",  # noqa: E501
                                         },
                                        {"name": "Service & Maintenance",
                                         "type": "professional_services",
                                         "description": "HVAC service, repair, preventive maintenance",  # noqa: E501
                                         },
                                        {"name": "Sheet Metal Services",
                                         "type": "construction_services",
                                         "description": "Sheet metal fabrication and installation",  # noqa: E501
                                         },
                                        {"name": "Plumbing Services",
                                         "type": "construction_services",
                                         "description": "Commercial plumbing systems",
                                         },
                                        ],
                   "research_notes": "TENTATIVE - Multiple entities: RoyalAire (FL, acquired by Comfort Systems USA 2017), Royal Mechanical (MN/WI/IA), others in AZ, Canada.",  # noqa: E501
                   },
                  {"vendor_name": "HALO BRANDED SOLUTIONS INC",
                   "industry": "Promotional Products",
                   "business_model": "B2B Distribution",
                   "typical_delivery": "Product sourcing + fulfillment",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Promotional products and branded merchandise - apparel, gifts, company stores, recognition programs",  # noqa: E501
                   "primary_products": [{"name": "Promotional Products",
                                         "type": "tangible_personal_property",
                                         "description": "Branded items: bags, drinkware, pens, novelties",  # noqa: E501
                                         },
                                        {"name": "Branded Apparel",
                                         "type": "tangible_personal_property",
                                         "description": "Custom embroidered/printed clothing",  # noqa: E501
                                         },
                                        {"name": "Company Stores",
                                         "type": "saas_subscription",
                                         "description": "Online branded merchandise portals",  # noqa: E501
                                         },
                                        {"name": "Recognition Programs",
                                         "type": "professional_services",
                                         "description": "Employee recognition and incentive programs",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Largest US promotional products distributor. 1,800 employees, 42 global offices. Owned by TPG Capital ($100B+ assets). Serves 100+ Fortune 500.",  # noqa: E501
                   },
                  {"vendor_name": "GLOBAL FACILITY MANAGEMENT &",
                   "industry": "Facilities Management",
                   "business_model": "B2B Services",
                   "typical_delivery": "On-site facility services",
                   "wa_tax_classification": "professional_services",
                   "product_description": "Multi-site facility management and construction - remodeling, repair, janitorial, restoration",  # noqa: E501
                   "primary_products": [{"name": "Building Maintenance",
                                         "type": "professional_services",
                                         "description": "HVAC, plumbing, electrical maintenance",  # noqa: E501
                                         },
                                        {"name": "Janitorial Services",
                                         "type": "professional_services",
                                         "description": "Commercial cleaning services",
                                         },
                                        {"name": "Remodel & Construction",
                                         "type": "construction_services",
                                         "description": "Multi-store retrofits and remodels",  # noqa: E501
                                         },
                                        {"name": "Restoration Services",
                                         "type": "professional_services",
                                         "description": "Emergency restoration and repairs",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Global Facility Management & Construction, Inc. Melville, NY. Provides 24/7/365 services throughout North America.",  # noqa: E501
                   },
                  {"vendor_name": "WACHTER INC",
                   "industry": "Technology & Electrical Integration",
                   "business_model": "B2B Services",
                   "typical_delivery": "On-site integration + construction",
                   "wa_tax_classification": "construction_services",
                   "product_description": "Technology integrator - electrical, IT networks, security, automation, audiovisual systems",  # noqa: E501
                   "primary_products": [{"name": "Electrical Systems",
                                         "type": "construction_services",
                                         "description": "Commercial electrical contracting and installation",  # noqa: E501
                                         },
                                        {"name": "IT Networks",
                                         "type": "professional_services",
                                         "description": "Network infrastructure design and installation",  # noqa: E501
                                         },
                                        {"name": "Physical Security",
                                         "type": "construction_services",
                                         "description": "Access control, surveillance systems",  # noqa: E501
                                         },
                                        {"name": "AV & Collaboration",
                                         "type": "construction_services",
                                         "description": "Conference room technology, audiovisual",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 1930. Family-owned, 4 generations. 1,400 W2 employees. Licensed in all 50 states. Serves Fortune 500. Based in Lenexa, KS.",  # noqa: E501
                   },
                  {"vendor_name": "FIREKING SECURITY PRODUCTS LLC",
                   "industry": "Security Storage Manufacturing",
                   "business_model": "B2B Manufacturing",
                   "typical_delivery": "Product manufacturing + distribution",
                   "wa_tax_classification": "tangible_personal_property",
                   "product_description": "Fireproof file cabinets and safes - UL-rated fire protection, burglary-rated security",  # noqa: E501
                   "primary_products": [{"name": "Fireproof File Cabinets",
                                         "type": "tangible_personal_property",
                                         "description": "2-hour UL fire-rated file cabinets, vertical/lateral",  # noqa: E501
                                         },
                                        {"name": "Security Safes",
                                         "type": "tangible_personal_property",
                                         "description": "Burglar fire safes, data media safes",  # noqa: E501
                                         },
                                        {"name": "Safe-in-a-File",
                                         "type": "tangible_personal_property",
                                         "description": "Concealed safe within file cabinet",  # noqa: E501
                                         },
                                        {"name": "Flammable Storage",
                                         "type": "tangible_personal_property",
                                         "description": "Flammable material safety cabinets",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 1951. New Albany, IN. Made in USA. UL-rated. Survives 30-ft loaded fall, 2000°F explosion test. Best Homes & Gardens award.",  # noqa: E501
                   },
                  {"vendor_name": "SOUTHWEST SIGN GROUP INC",
                   "industry": "Signage Manufacturing",
                   "business_model": "B2B Manufacturing & Services",
                   "typical_delivery": "Manufacturing + installation",
                   "wa_tax_classification": "construction_services",
                   "product_description": "National signage programs - manufacturing, installation, maintenance for multi-location brands",  # noqa: E501
                   "primary_products": [{"name": "Sign Manufacturing",
                                         "type": "tangible_personal_property",
                                         "description": "In-house sign manufacturing, cutting-edge technology",  # noqa: E501
                                         },
                                        {"name": "National Installations",
                                         "type": "construction_services",
                                         "description": "Multi-location sign installation programs",  # noqa: E501
                                         },
                                        {"name": "Sign Maintenance",
                                         "type": "professional_services",
                                         "description": "Ongoing sign service and maintenance",  # noqa: E501
                                         },
                                        {"name": "Regional Programs",
                                         "type": "professional_services",
                                         "description": "Regional signage program management",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 1946. San Antonio, TX. 30+ years experience. Complete in-house manufacturing unlike outsourcing competitors.",  # noqa: E501
                   },
                  {"vendor_name": "SEQUOYAH ELECTRIC LLC",
                   "industry": "Electrical & Low Voltage Construction",
                   "business_model": "B2B Services",
                   "typical_delivery": "On-site electrical construction",
                   "wa_tax_classification": "construction_services",
                   "product_description": "Electrical and low voltage engineering and construction - commercial, data centers, structured cabling",  # noqa: E501
                   "primary_products": [{"name": "Electrical Construction",
                                         "type": "construction_services",
                                         "description": "Commercial electrical design-build and construction",  # noqa: E501
                                         },
                                        {"name": "Low Voltage Systems",
                                         "type": "construction_services",
                                         "description": "Data center, security, structured cabling installations",  # noqa: E501
                                         },
                                        {"name": "24/7 Service",
                                         "type": "professional_services",
                                         "description": "Emergency electrical and network services",  # noqa: E501
                                         },
                                        {"name": "Engineering & Preconstruction",
                                         "type": "professional_services",
                                         "description": "Electrical engineering and project planning",  # noqa: E501
                                         },
                                        ],
                   "research_notes": "Founded 1988. Redmond, WA. Licensed in WA, OR, ID, CA, NY, TX. WA's 100 Best Companies 12 consecutive years (2014-2025).",  # noqa: E501
                   },
                  ]

# Continuing with more vendors...
BATCH3_VENDORS.extend([{"vendor_name": "HORIZON RETAIL CONSTRUCTION INC",
                        "industry": "Retail Construction",
                        "business_model": "B2B General Contracting",
                        "typical_delivery": "On-site construction services",
                        "wa_tax_classification": "construction_services",
                        "product_description": "Multi-site retail tenant improvement - buildouts, rollouts, remodels for national brands",  # noqa: E501
                        "primary_products": [{"name": "Store Buildouts",
                                               "type": "construction_services",
                                               "description": "New store construction and tenant improvements",  # noqa: E501
                                              },
                                             {"name": "Multi-Store Rollouts",
                                              "type": "construction_services",
                                              "description": "National rollout program management",  # noqa: E501
                                              },
                                             {"name": "Remodels & Rebranding",
                                              "type": "construction_services",
                                              "description": "Store refresh and rebranding projects",  # noqa: E501
                                              },
                                             {"name": "Turnkey Construction",
                                              "type": "construction_services",
                                              "description": "Pre-construction through post-construction",  # noqa: E501
                                              },
                                             ],
                        "research_notes": "Founded 1993. Sturtevant, WI. Licensed all 50 states. Serves retail, financial, healthcare, restaurants. Clients: Best Buy, Foot Locker, Planet Fitness.",  # noqa: E501
                        },
                       {"vendor_name": "MDS BUILDERS INC",
                        "industry": "Commercial Construction",
                        "business_model": "B2B General Contracting",
                        "typical_delivery": "On-site construction management",
                        "wa_tax_classification": "construction_services",
                        "product_description": "Commercial general contractor - tenant construction, rollouts, facilities maintenance",  # noqa: E501
                        "primary_products": [{"name": "General Contracting",
                                              "type": "construction_services",
                                              "description": "Commercial construction and renovation",  # noqa: E501
                                              },
                                             {"name": "Construction Management",
                                              "type": "professional_services",
                                              "description": "Project administration and scheduling",  # noqa: E501
                                              },
                                             {"name": "Rollouts & Rebranding",
                                              "type": "construction_services",
                                              "description": "Multi-location program administration",  # noqa: E501
                                              },
                                             {"name": "Facilities Maintenance",
                                              "type": "professional_services",
                                              "description": "Ongoing facility maintenance services",  # noqa: E501
                                              },
                                             ],
                        "research_notes": "Founded 1989. Boca Raton, FL (HQ) + Austin, TX + Medina, OH. 5,000+ projects in 46 states. AGC & CASF member.",  # noqa: E501
                        },
                       {"vendor_name": "DELOITTE CONSULTING LLP",
                        "industry": "Management Consulting",
                        "business_model": "B2B Professional Services",
                        "typical_delivery": "Professional consulting services",
                        "wa_tax_classification": "professional_services",
                        "product_description": "Global consulting - strategy, technology, operations, human capital, financial advisory",  # noqa: E501
                        "primary_products": [{"name": "Technology Consulting",
                                              "type": "professional_services",
                                              "description": "IT services, digital transformation, AI implementation",  # noqa: E501
                                              },
                                             {"name": "Strategy & Analytics",
                                              "type": "professional_services",
                                              "description": "Business strategy, M&A, analytics consulting",  # noqa: E501
                                              },
                                             {"name": "Operations Consulting",
                                              "type": "professional_services",
                                              "description": "Core business operations optimization",  # noqa: E501
                                              },
                                             {"name": "Human Capital",
                                              "type": "professional_services",
                                              "description": "HR transformation, workforce strategy",  # noqa: E501
                                              },
                                             ],
                        "research_notes": "World's largest consulting org. $1B AI investment. Generative AI practice. Serves technology, financial, healthcare, government sectors.",  # noqa: E501
                        },
                       {"vendor_name": "LOCKTON COMPANIES",
                        "industry": "Insurance Brokerage",
                        "business_model": "B2B Financial Services",
                        "typical_delivery": "Insurance placement + risk consulting",
                        "wa_tax_classification": "professional_services",
                        "product_description": "Insurance brokerage and risk management - property/casualty, employee benefits, retirement",  # noqa: E501
                        "primary_products": [{"name": "Property & Casualty Insurance",
                                              "type": "professional_services",
                                              "description": "Commercial P&C insurance placement",  # noqa: E501
                                              },
                                             {"name": "Risk Management",
                                              "type": "professional_services",
                                              "description": "Risk control, analytics, claims consulting",  # noqa: E501
                                              },
                                             {"name": "Employee Benefits",
                                              "type": "professional_services",
                                              "description": "Health, welfare, retirement benefits consulting",  # noqa: E501
                                              },
                                             {"name": "Surety & Executive Risk",
                                              "type": "professional_services",
                                              "description": "Surety bonds, cyber risk, executive risk",  # noqa: E501
                                              },
                                             ],
                        "research_notes": "Founded 1966. Kansas City, MO. World's largest privately held insurance broker. 10,750+ associates. 130+ offices, 140+ countries.",  # noqa: E501
                        },
                       {"vendor_name": "FIRST AD SIGNS",
                        "industry": "Signage & Outdoor Advertising",
                        "business_model": "B2B Services",
                        "typical_delivery": "Manufacturing + installation",
                        "wa_tax_classification": "construction_services",
                        "product_description": "Outdoor advertising and signage solutions (tentative - limited data)",  # noqa: E501
                        "primary_products": [{"name": "Outdoor Signage",
                                              "type": "tangible_personal_property",
                                              "description": "Billboards, outdoor advertising media",  # noqa: E501
                                              },
                                             {"name": "Sign Installation",
                                              "type": "construction_services",
                                              "description": "Outdoor sign installation services",  # noqa: E501
                                              },
                                             ],
                        "research_notes": "TENTATIVE DATA - Specific company not found in search results. Industry inferred from name pattern. Needs additional research.",  # noqa: E501
                        },
                       {"vendor_name": "STALEY INC",
                        "industry": "Electrical Services",
                        "business_model": "B2B Services",
                        "typical_delivery": "Electrical contracting services",
                        "wa_tax_classification": "construction_services",
                        "product_description": "Electrical contractor - commercial and residential electrical services (tentative)",  # noqa: E501
                        "primary_products": [{"name": "Commercial Electrical",
                                              "type": "construction_services",
                                              "description": "Commercial electrical installation and service",  # noqa: E501
                                              },
                                             {"name": "Residential Electrical",
                                              "type": "construction_services",
                                              "description": "Residential electrical services",  # noqa: E501
                                              },
                                             {"name": "Audio Visual",
                                              "type": "construction_services",
                                              "description": "AV system installation",
                                              },
                                             ],
                        "research_notes": "TENTATIVE - Multiple Staley Electric companies found (Pittsburgh PA, Little Rock AR, Bonney Lake WA). One Staley Electric Supply in Conshohocken PA (wholesale).",  # noqa: E501
                        },
                       {"vendor_name": "DELUXE SMALL BUSINESS SALES INC",
                        "industry": "Business Products & Printing",
                        "business_model": "B2B Distribution",
                        "typical_delivery": "Printed products + digital services",
                        "wa_tax_classification": "tangible_personal_property",
                        "product_description": "Business checks and forms printing - checks, promotional products, payment processing",  # noqa: E501
                        "primary_products": [{"name": "Business Checks",
                                              "type": "tangible_personal_property",
                                              "description": "Custom printed business checks, deposit slips",  # noqa: E501
                                              },
                                             {"name": "Business Forms",
                                              "type": "tangible_personal_property",
                                              "description": "Custom business forms and office supplies",  # noqa: E501
                                              },
                                             {"name": "Promotional Products",
                                              "type": "tangible_personal_property",
                                              "description": "Branded promotional items",  # noqa: E501
                                              },
                                             {"name": "Payment Services",
                                              "type": "professional_services",
                                              "description": "Payment processing and data services",  # noqa: E501
                                              },
                                             ],
                        "research_notes": "Deluxe Corporation subsidiary. 100+ years check printing. 4,000+ financial institutions. Minneapolis HQ. High security fraud-deterrent features.",  # noqa: E501
                        },
                       {"vendor_name": "HH ASSOCIATES US INC",
                        "industry": "Creative Production & Procurement",
                        "business_model": "B2B Services",
                        "typical_delivery": "Managed services + technology platform",
                        "wa_tax_classification": "professional_services",
                        "product_description": "Global creative production and marketing procurement - managed services, sustainability solutions",  # noqa: E501
                        "primary_products": [{"name": "Creative Production",
                                              "type": "professional_services",
                                              "description": "Marketing creative production services",  # noqa: E501
                                              },
                                             {"name": "Procurement Services",
                                              "type": "professional_services",
                                              "description": "Marketing supply chain procurement",  # noqa: E501
                                              },
                                             {"name": "Technology Platform",
                                              "type": "saas_subscription",
                                              "description": "Proprietary marketing optimization technology",  # noqa: E501
                                              },
                                             {"name": "Sustainability Solutions",
                                              "type": "professional_services",
                                              "description": "Environmental measurement, CO2 impact tracking",  # noqa: E501
                                              },
                                             ],
                        "research_notes": "HH Global. Chicago, IL. 160 employees, $50.6M revenue. Serves 110+ countries. Tech-enabled creative production for global brands.",  # noqa: E501
                        },
                       {"vendor_name": "SHAFFER WILSON SARVER & GRAY PC",
                        "industry": "Accounting & Tax Services",
                        "business_model": "B2B Professional Services",
                        "typical_delivery": "Professional accounting services",
                        "wa_tax_classification": "professional_services",
                        "product_description": "CPA firm - accounting, audit, tax services (limited data)",  # noqa: E501
                        "primary_products": [{"name": "Accounting Services",
                                              "type": "professional_services",
                                              "description": "Business accounting and bookkeeping",  # noqa: E501
                                              },
                                             {"name": "Tax Services",
                                              "type": "professional_services",
                                              "description": "Corporate and business tax preparation",  # noqa: E501
                                              },
                                             {"name": "Audit Services",
                                              "type": "professional_services",
                                              "description": "Financial audit and assurance",  # noqa: E501
                                              },
                                             ],
                        "research_notes": "TENTATIVE DATA - Limited information found. Presence on LinkedIn and Glassdoor confirmed. Specific services and location unclear. Needs verification.",  # noqa: E501
                        },
                       {"vendor_name": "PROSIGNS LLC",
                        "industry": "Signage Manufacturing",
                        "business_model": "B2B Manufacturing & Services",
                        "typical_delivery": "Manufacturing + installation",
                        "wa_tax_classification": "construction_services",
                        "product_description": "Professional custom signage - banners, channel letters, vehicle wraps, graphics",  # noqa: E501
                        "primary_products": [{"name": "Custom Signs",
                                              "type": "tangible_personal_property",
                                              "description": "Banners, channel letters, box signs",  # noqa: E501
                                              },
                                             {"name": "Vehicle Graphics",
                                              "type": "tangible_personal_property",
                                              "description": "Vehicle wraps and graphics",  # noqa: E501
                                              },
                                             {"name": "Sign Installation",
                                              "type": "construction_services",
                                              "description": "Professional sign installation services",  # noqa: E501
                                              },
                                             {"name": "Large Format Printing",
                                              "type": "professional_services",
                                              "description": "CNC routing, digital printing",  # noqa: E501
                                              },
                                             ],
                        "research_notes": "TENTATIVE - Dearborn, MI location. Multiple Pro Signs entities nationwide (Downingtown PA founded 1947, 80K sq ft facility). Regional operators.",  # noqa: E501
                        },
                       {"vendor_name": "EPLUS TECHNOLOGY INC",
                        "industry": "IT Solutions & Services",
                        "business_model": "B2B VAR",
                        "typical_delivery": "Technology resale + professional services",
                        "wa_tax_classification": "tangible_personal_property",
                        "product_description": "IT solutions provider - hardware, cloud, security, managed services, financing",  # noqa: E501
                        "primary_products": [{"name": "IT Hardware",
                                              "type": "tangible_personal_property",
                                              "description": "Servers, storage, networking equipment (Cisco, Dell, HPE)",  # noqa: E501
                                              },
                                             {"name": "Cloud Solutions",
                                              "type": "iaas_paas",
                                              "description": "Cloud migration, infrastructure, data center",  # noqa: E501
                                              },
                                             {"name": "Security Solutions",
                                              "type": "saas_subscription",
                                              "description": "Cybersecurity products and services",  # noqa: E501
                                              },
                                             {"name": "Professional Services",
                                              "type": "professional_services",
                                              "description": "IT consulting, implementation, managed services",  # noqa: E501
                                              },
                                             ],
                        "research_notes": "Founded 1990. Herndon, VA. Public (NASDAQ: PLUS). 2,100+ employees. 5,000+ customers. 95% US revenue. Serves Fortune 500.",  # noqa: E501
                        },
                       {"vendor_name": "ANDERSEN CONSTRUCTION COMPANY OF",
                        "industry": "Commercial Construction",
                        "business_model": "B2B General Contracting",
                        "typical_delivery": "On-site construction services",
                        "wa_tax_classification": "construction_services",
                        "product_description": "General contractor - commercial construction, healthcare, education, multi-family",  # noqa: E501
                        "primary_products": [{"name": "General Contracting",
                                              "type": "construction_services",
                                              "description": "Commercial construction projects",  # noqa: E501
                                              },
                                             {"name": "Design-Build",
                                              "type": "construction_services",
                                              "description": "Integrated design-build services",  # noqa: E501
                                              },
                                             {"name": "Construction Management",
                                              "type": "professional_services",
                                              "description": "CM/GC, IPD project delivery",  # noqa: E501
                                              },
                                             {"name": "Tenant Improvements",
                                              "type": "construction_services",
                                              "description": "Complex occupied campus projects",  # noqa: E501
                                              },
                                             ],
                        "research_notes": "TENTATIVE - Andersen Construction (Portland OR, founded 1950) or ANDERSON Construction (Ventura/Santa Barbara CA, 90+ years). Family-owned options.",  # noqa: E501
                        },
                       {"vendor_name": "CONVERGENT MEDIA SYSTEMS",
                        "industry": "Digital Signage & AV",
                        "business_model": "B2B Services",
                        "typical_delivery": "Cloud platform + installation",
                        "wa_tax_classification": "professional_services",
                        "product_description": "Digital signage and audiovisual integration - content management, interactive experiences",  # noqa: E501
                        "primary_products": [{"name": "Digital Signage",
                                              "type": "saas_subscription",
                                              "description": "Cloud-based digital media platform",  # noqa: E501
                                              },
                                             {"name": "Content Creation",
                                              "type": "professional_services",
                                              "description": "Dynamic content creation and management",  # noqa: E501
                                              },
                                             {"name": "AV Integration",
                                              "type": "construction_services",
                                              "description": "Audiovisual system integration",  # noqa: E501
                                              },
                                             {"name": "Interactive Solutions",
                                              "type": "saas_subscription",
                                              "description": "Kiosks, video communications, touchless control",  # noqa: E501
                                              },
                                             ],
                        "research_notes": "Now SageNet company. 35 years innovation. Alpharetta, GA. Ballantyne Strong company. BrightSign partner. SafeStore Screen Control product.",  # noqa: E501
                        },
                       {"vendor_name": "AUTOMOTIVE RENTALS INC",
                        "industry": "Fleet Management Services",
                        "business_model": "B2B Services",
                        "typical_delivery": "Vehicle rental + fleet management",
                        "wa_tax_classification": "professional_services",
                        "product_description": "Government fleet management - vehicle rental, leasing, fuel, maintenance, telematics",  # noqa: E501
                        "primary_products": [{"name": "Vehicle Rental",
                                              "type": "professional_services",
                                              "description": "Federal government vehicle rental services",  # noqa: E501
                                              },
                                             {"name": "Fleet Leasing",
                                              "type": "professional_services",
                                              "description": "Vehicle leasing and acquisition",  # noqa: E501
                                              },
                                             {"name": "Fuel & Maintenance",
                                              "type": "professional_services",
                                              "description": "Fuel management and vehicle maintenance",  # noqa: E501
                                              },
                                             {"name": "Telematics",
                                              "type": "saas_subscription",
                                              "description": "Fleet telematics and tracking technology",  # noqa: E501
                                              },
                                             ],
                        "research_notes": "Woman-owned small business. Serves federal government. Fleet management with strategic consulting. Garage management, licensing services.",  # noqa: E501
                        },
                       {"vendor_name": "BURR COMPUTER ENVIRONMENTS INC",
                        "industry": "Data Center Construction",
                        "business_model": "B2B Services",
                        "typical_delivery": "Engineering + construction services",
                        "wa_tax_classification": "construction_services",
                        "product_description": "Data center design and construction - IT facilities planning, design-build, infrastructure",  # noqa: E501
                        "primary_products": [{"name": "Data Center Design",
                                              "type": "professional_services",
                                              "description": "IT facility planning and engineering",  # noqa: E501
                                              },
                                             {"name": "Construction Services",
                                              "type": "construction_services",
                                              "description": "Data center construction and build-out",  # noqa: E501
                                              },
                                             {"name": "Site Services",
                                              "type": "professional_services",
                                              "description": "Integrated site services for computing environments",  # noqa: E501
                                              },
                                             {"name": "Master Planning",
                                              "type": "professional_services",
                                              "description": "Site audit and long-term facility planning",  # noqa: E501
                                              },
                                             ],
                        "research_notes": "Founded 1988. Houston, TX. BCEI. Industry leader for Fortune 500 IT facilities. Two-phased approach: audit + master plan, then implementation.",  # noqa: E501
                        },
                       ])


def update_vendors():
    """Update Batch 3 vendors in Supabase"""

    print("Connecting to Supabase...")
    supabase = get_supabase_client()
    print("✓ Connected\n")

    print(f"Updating Batch 3: {len(BATCH3_VENDORS)} vendors (41-65)...\n")

    updated = 0
    errors = 0

    for vendor_data in BATCH3_VENDORS:
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
    print("BATCH 3 UPDATE COMPLETE")
    print(f"{'=' * 70}")
    print(f"✓ Updated: {updated}")
    print(f"❌ Errors: {errors}")
    print(f"Total researched so far: {40 + updated} vendors")
    print(f"Remaining: {294 - 40 - updated} vendors")


if __name__ == "__main__":
    update_vendors()
