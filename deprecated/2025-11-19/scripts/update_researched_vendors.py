#!/usr/bin/env python3
"""
Update Supabase with researched vendor data
"""

from core.database import get_supabase_client
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Researched vendor data
RESEARCHED_VENDORS = [{"vendor_name": "MOREDIRECT INC",
                       "industry": "IT Distribution & E-commerce",
                       "business_model": "B2B/B2G Wholesale Distribution",
                       "typical_delivery": "Physical shipment + digital procurement platform",  # noqa: E501
                       "wa_tax_classification": "tangible_personal_property",
                       "product_description": "IT equipment wholesale distributor - computers, servers, networking, software, peripherals",  # noqa: E501
                       "primary_products": [{"name": "Computer Hardware",
                                             "type": "tangible_personal_property",
                                             "description": "Notebooks, desktops, servers, storage products",  # noqa: E501
                                             },
                                            {"name": "Networking Equipment",
                                             "type": "tangible_personal_property",
                                             "description": "Network hardware, switches, routers",  # noqa: E501
                                             },
                                            {"name": "Software Licenses",
                                             "type": "software_license",
                                             "description": "Enterprise software licensing",  # noqa: E501
                                             },
                                            {"name": "E-Procurement Platform",
                                             "type": "saas_subscription",
                                             "description": "Web-based procurement solution",  # noqa: E501
                                             },
                                            ],
                       "research_notes": "Aggregates 350,000+ products from IT distributors/manufacturers. Serves corporate and government customers. Based in Boca Raton, FL.",  # noqa: E501
                       },
                      {"vendor_name": "ZONES INC",
                       "industry": "IT Solutions & Services",
                       "business_model": "B2B IT Solutions Provider",
                       "typical_delivery": "Mixed - physical hardware + cloud services + professional services",  # noqa: E501
                       "wa_tax_classification": "mixed_classification",
                       "product_description": "Global IT solutions provider - hardware, cloud, networking, security, managed services",  # noqa: E501
                       "primary_products": [{"name": "Workplace Modernization",
                                             "type": "professional_services",
                                             "description": "Digital workplace solutions and consulting",  # noqa: E501
                                             },
                                            {"name": "Network Optimization",
                                             "type": "professional_services",
                                             "description": "Network design and implementation services",  # noqa: E501
                                             },
                                            {"name": "Cloud & Data Center",
                                             "type": "iaas_paas",
                                             "description": "Cloud migration and data center services",  # noqa: E501
                                             },
                                            {"name": "Cybersecurity Solutions",
                                             "type": "saas_subscription",
                                             "description": "Security products and services",  # noqa: E501
                                             },
                                            {"name": "Hardware Products",
                                             "type": "tangible_personal_property",
                                             "description": "150,000+ products from manufacturers",  # noqa: E501
                                             },
                                            ],
                       "research_notes": "Founded 1986, headquartered Auburn WA. Operates in 120+ countries. Minority Business Enterprise (MBE). Partnerships: Microsoft, Apple, Cisco, Lenovo.",  # noqa: E501
                       },
                      {"vendor_name": "MC SIGN COMPANY",
                       "industry": "Signage & Facility Services",
                       "business_model": "B2B Services",
                       "typical_delivery": "On-site installation and services",
                       "wa_tax_classification": "construction_services",
                       "product_description": "National signage company - design, manufacturing, installation, maintenance of commercial signs",  # noqa: E501
                       "primary_products": [{"name": "Sign Design & Engineering",
                                             "type": "professional_services",
                                             "description": "Custom sign design and engineering services",  # noqa: E501
                                             },
                                            {"name": "Sign Manufacturing",
                                             "type": "manufacturing",
                                             "description": "Signage, lighting, electrical sign production",  # noqa: E501
                                             },
                                            {"name": "Installation Services",
                                             "type": "construction_services",
                                             "description": "Sign installation and permitting",  # noqa: E501
                                             },
                                            {"name": "Maintenance Services",
                                             "type": "professional_services",
                                             "description": "Ongoing sign service and repair",  # noqa: E501
                                             },
                                            ],
                       "research_notes": "Rebranded to MC Group in 2018. 57+ years experience. Based in Mentor, OH. One of largest full-service sign companies in US.",  # noqa: E501
                       },
                      {"vendor_name": "SOUTH WATER SIGNS",
                       "industry": "Signage Manufacturing & Services",
                       "business_model": "B2B Services",
                       "typical_delivery": "Manufacturing + on-site installation",
                       "wa_tax_classification": "construction_services",
                       "product_description": "Full-service turnkey signage provider - manufacturing, installation, maintenance",  # noqa: E501
                       "primary_products": [{"name": "Interior Signage",
                                             "type": "tangible_personal_property",
                                             "description": "Custom interior signs and graphics",  # noqa: E501
                                             },
                                            {"name": "Exterior Signage",
                                             "type": "tangible_personal_property",
                                             "description": "Channel letters, illuminated signs, monuments",  # noqa: E501
                                             },
                                            {"name": "Installation Services",
                                             "type": "construction_services",
                                             "description": "National installation and permitting",  # noqa: E501
                                             },
                                            {"name": "Project Management",
                                             "type": "professional_services",
                                             "description": "Design, planning, coordination",  # noqa: E501
                                             },
                                            ],
                       "research_notes": "Based in Elmhurst, IL. Specializes in airports, retail, stadiums. Revenue $38.4M, 127 employees. May be closed per Yelp.",  # noqa: E501
                       },
                      {"vendor_name": "OFFICE DEPOT INC",
                       "industry": "Office Supplies Retail",
                       "business_model": "B2B/B2C Retail",
                       "typical_delivery": "Physical shipment + retail stores",
                       "wa_tax_classification": "tangible_personal_property",
                       "product_description": "Office supply retailer - office products, furniture, technology, business services",  # noqa: E501
                       "primary_products": [{"name": "Office Supplies",
                                             "type": "tangible_personal_property",
                                             "description": "Paper, ink, toner, files, organizational products",  # noqa: E501
                                             },
                                            {"name": "Office Furniture",
                                             "type": "tangible_personal_property",
                                             "description": "Desks, chairs, filing cabinets",  # noqa: E501
                                             },
                                            {"name": "Technology Products",
                                             "type": "tangible_personal_property",
                                             "description": "Computers, printers, electronics",  # noqa: E501
                                             },
                                            {"name": "Business Services",
                                             "type": "professional_services",
                                             "description": "Printing, tech services, furniture assembly",  # noqa: E501
                                             },
                                            ],
                       "research_notes": "ODP Corporation. 922 retail stores in US. Headquartered Boca Raton, FL. Operates Office Depot and OfficeMax brands.",  # noqa: E501
                       },
                      {"vendor_name": "ALLEN INDUSTRIES INC",
                       "industry": "Signage Manufacturing",
                       "business_model": "B2B Manufacturing & Services",
                       "typical_delivery": "Manufacturing + installation services",
                       "wa_tax_classification": "construction_services",
                       "product_description": "Full-service signage and architectural elements manufacturer",  # noqa: E501
                       "primary_products": [{"name": "Custom Signage",
                                             "type": "tangible_personal_property",
                                             "description": "Commercial signs and advertising specialties",  # noqa: E501
                                             },
                                            {"name": "Architectural Elements",
                                             "type": "tangible_personal_property",
                                             "description": "Building elements and brand installations",  # noqa: E501
                                             },
                                            {"name": "Installation Services",
                                             "type": "construction_services",
                                             "description": "Sign installation and maintenance",  # noqa: E501
                                             },
                                            {"name": "Project Management",
                                             "type": "professional_services",
                                             "description": "Design, engineering, project coordination",  # noqa: E501
                                             },
                                            ],
                       "research_notes": "Founded 1931. Facilities in NC, FL, AZ, OH. Serves retail, QSR, petroleum, financial, healthcare sectors.",  # noqa: E501
                       },
                      {"vendor_name": "COAST SIGN INCORPORATED",
                       "industry": "Signage Manufacturing & Services",
                       "business_model": "B2B National Services",
                       "typical_delivery": "Manufacturing + nationwide installation",
                       "wa_tax_classification": "construction_services",
                       "product_description": "National signage solutions - design, manufacturing, installation, maintenance",  # noqa: E501
                       "primary_products": [{"name": "Channel Letters & Monuments",
                                             "type": "tangible_personal_property",
                                             "description": "Electrical signage, pylons, monument boards",  # noqa: E501
                                             },
                                            {"name": "ATM Products",
                                             "type": "tangible_personal_property",
                                             "description": "ATM surrounds and kiosks",
                                             },
                                            {"name": "Installation Services",
                                             "type": "construction_services",
                                             "description": "Nationwide installation and permitting",  # noqa: E501
                                             },
                                            {"name": "Maintenance Services",
                                             "type": "professional_services",
                                             "description": "Post-installation service and repair",  # noqa: E501
                                             },
                                            ],
                       "research_notes": "Founded 1964. 100,000 sq ft facility in Anaheim, CA. Serves all 50 states. Multi-location brands: restaurants, hotels, retail, financial. Acquired by CapitalSpring 2025.",  # noqa: E501
                       },
                      {"vendor_name": "TRIANGLE SIGN AND SERVICE LLC",
                       "industry": "Signage & Lighting Services",
                       "business_model": "B2B Services",
                       "typical_delivery": "On-site installation and services",
                       "wa_tax_classification": "construction_services",
                       "product_description": "Custom signage and lighting design, installation, maintenance",  # noqa: E501
                       "primary_products": [{"name": "Custom Signage",
                                             "type": "tangible_personal_property",
                                             "description": "Interior and exterior custom signs",  # noqa: E501
                                             },
                                            {"name": "Lighting Products",
                                             "type": "tangible_personal_property",
                                             "description": "Interior and exterior lighting systems",  # noqa: E501
                                             },
                                            {"name": "Installation Services",
                                             "type": "construction_services",
                                             "description": "Installation and permitting coordination",  # noqa: E501
                                             },
                                            {"name": "Maintenance Services",
                                             "type": "professional_services",
                                             "description": "Repair and maintenance services",  # noqa: E501
                                             },
                                            ],
                       "research_notes": "Operates as Persona Triangle. Headquarters in Watertown SD and Baltimore MD. 260,000 sq ft manufacturing. Serves hospitality, retail, healthcare, stadiums. Revenue $38.4M.",  # noqa: E501
                       },
                      {"vendor_name": "HCL AMERICA INC",
                       "industry": "IT Services & Consulting",
                       "business_model": "B2B IT Services",
                       "typical_delivery": "Professional services + cloud solutions",
                       "wa_tax_classification": "professional_services",
                       "product_description": "IT consulting and services - digital transformation, cloud, engineering, software",  # noqa: E501
                       "primary_products": [{"name": "IT Consulting Services",
                                             "type": "professional_services",
                                             "description": "IT consulting, infrastructure management, application development",  # noqa: E501
                                             },
                                            {"name": "Cloud Services",
                                             "type": "iaas_paas",
                                             "description": "CloudSMART offerings, cloud migration and optimization",  # noqa: E501
                                             },
                                            {"name": "Engineering Services",
                                             "type": "professional_services",
                                             "description": "Engineering and R&D services, product development",  # noqa: E501
                                             },
                                            {"name": "Software Products",
                                             "type": "software_license",
                                             "description": "HCL AppScan, BigFix, Connections, Notes, Unica",  # noqa: E501
                                             },
                                            ],
                       "research_notes": "HCLTech - Indian multinational. 220,000+ employees in 60 countries. Headquartered Noida, India. Three segments: ITBS, ERS, HCLSoftware.",  # noqa: E501
                       },
                      {"vendor_name": "WALTON SIGNAGE LTD",
                       "industry": "Signage Solutions",
                       "business_model": "B2B Services",
                       "typical_delivery": "Turnkey signage solutions + installation",
                       "wa_tax_classification": "construction_services",
                       "product_description": "Turnkey signage solutions and program management for national brands",  # noqa: E501
                       "primary_products": [{"name": "Custom Signage",
                                             "type": "tangible_personal_property",
                                             "description": "Interior, exterior, electronic message displays",  # noqa: E501
                                             },
                                            {"name": "Brand Implementation",
                                             "type": "professional_services",
                                             "description": "Program management and brand rollout",  # noqa: E501
                                             },
                                            {"name": "Installation Services",
                                             "type": "construction_services",
                                             "description": "Nationwide installation and maintenance",  # noqa: E501
                                             },
                                            {"name": "Additional Services",
                                             "type": "professional_services",
                                             "description": "LED retrofits, EV charging, striping",  # noqa: E501
                                             },
                                            ],
                       "research_notes": "Founded 1934 (4 generations). $40M+ revenue. San Antonio, TX. Inc. 5000 fastest-growing 5x. Serves restaurant, retail, banking, healthcare, petroleum sectors.",  # noqa: E501
                       },
                      {"vendor_name": "IMAGE NATIONAL INC",
                       "industry": "Printing & Imaging Services",
                       "business_model": "B2B Services",
                       "typical_delivery": "Printing and imaging services",
                       "wa_tax_classification": "professional_services",
                       "product_description": "Printing and imaging solutions (tentative - needs verification)",  # noqa: E501
                       "primary_products": [{"name": "Printing Services",
                                             "type": "professional_services",
                                             "description": "Commercial printing services",  # noqa: E501
                                             },
                                            {"name": "Imaging Solutions",
                                             "type": "professional_services",
                                             "description": "Document imaging and management",  # noqa: E501
                                             },
                                            ],
                       "research_notes": "TENTATIVE DATA - exact company not confirmed. May be National Imaging Systems or similar. Needs follow-up research with location/industry details.",  # noqa: E501
                       },
                      {"vendor_name": "KEYSTONE MANAGEMENT INC",
                       "industry": "Property Management",
                       "business_model": "B2B Services",
                       "typical_delivery": "Property management services",
                       "wa_tax_classification": "professional_services",
                       "product_description": "Property and asset management services",
                       "primary_products": [{"name": "Property Management",
                                             "type": "professional_services",
                                             "description": "Residential and commercial property management",  # noqa: E501
                                             },
                                            {"name": "Asset Management",
                                             "type": "professional_services",
                                             "description": "Maintenance and asset management services",  # noqa: E501
                                             },
                                            {"name": "HOA Management",
                                             "type": "professional_services",
                                             "description": "Community association management",  # noqa: E501
                                             },
                                            ],
                       "research_notes": "Multiple Keystone entities exist. Specific company unclear without additional identifiers (location, specific services). Needs verification.",  # noqa: E501
                       },
                      {"vendor_name": "WALTON ENTERPRISES LTD",
                       "industry": "Family Office / Diversified",
                       "business_model": "Private Family Office",
                       "typical_delivery": "Varies by entity",
                       "wa_tax_classification": "professional_services",
                       "product_description": "Family office and diversified holdings",
                       "primary_products": [{"name": "Financial Services",
                                             "type": "professional_services",
                                             "description": "Family office treasury, accounting, tax services",  # noqa: E501
                                             },
                                            {"name": "Administrative Services",
                                             "type": "professional_services",
                                             "description": "Personal and business administrative support",  # noqa: E501
                                             },
                                            ],
                       "research_notes": "Walton family (Walmart) private office. Multiple Walton entities exist globally. Specific entity unclear. May also be signage-related Walton company.",  # noqa: E501
                       },
                      {"vendor_name": "BLAIR COMPANIES",
                       "industry": "Printing & Direct Mail",
                       "business_model": "B2B Services",
                       "typical_delivery": "Printing and mailing services",
                       "wa_tax_classification": "professional_services",
                       "product_description": "Printing and direct mail services (tentative)",  # noqa: E501
                       "primary_products": [{"name": "Printing Services",
                                             "type": "professional_services",
                                             "description": "Commercial printing",
                                             },
                                            {"name": "Direct Mail Services",
                                             "type": "professional_services",
                                             "description": "Direct mail marketing and fulfillment",  # noqa: E501
                                             },
                                            ],
                       "research_notes": "TENTATIVE DATA - specific Blair Companies not found in search results. Industry inferred from name pattern. Needs additional research.",  # noqa: E501
                       },
                      {"vendor_name": "SUNRISE BANKS NA",
                       "industry": "Banking & Financial Services",
                       "business_model": "Community Banking",
                       "typical_delivery": "Financial services delivery",
                       "wa_tax_classification": "financial_services",
                       "product_description": "Community bank - personal and business banking, lending, digital banking",  # noqa: E501
                       "primary_products": [{"name": "Personal Banking",
                                             "type": "financial_services",
                                             "description": "Checking, savings, credit builder, debit/credit cards",  # noqa: E501
                                             },
                                            {"name": "Business Banking",
                                             "type": "financial_services",
                                             "description": "Business checking, savings, commercial lending",  # noqa: E501
                                             },
                                            {"name": "Digital Banking",
                                             "type": "saas_subscription",
                                             "description": "Online and mobile banking platform",  # noqa: E501
                                             },
                                            {"name": "Specialized Lending",
                                             "type": "financial_services",
                                             "description": "SBA lending, New Markets Tax Credits",  # noqa: E501
                                             },
                                            ],
                       "research_notes": "Minneapolis/St. Paul, Sioux Falls locations. B Corporation. CDFI certified. Socially responsible community bank. Prepaid card division.",  # noqa: E501
                       },
                      ]


def update_vendors():
    """Update vendors in Supabase"""

    print("Connecting to Supabase...")
    supabase = get_supabase_client()
    print("✓ Connected\n")

    print(f"Updating {len(RESEARCHED_VENDORS)} vendors...\n")

    updated = 0
    errors = 0

    for vendor_data in RESEARCHED_VENDORS:
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
            print(f"  Industry: {vendor_data['industry']}")
            print(f"  WA Tax: {vendor_data['wa_tax_classification']}")
            print(f"  Products: {len(vendor_data['primary_products'])}")
            print()

            updated += 1

        except Exception as e:
            print(f"❌ {vendor_name} - Error: {e}\n")
            errors += 1

    print(f"\n{'=' * 70}")
    print("UPDATE COMPLETE")
    print(f"{'=' * 70}")
    print(f"✓ Updated: {updated}")
    print(f"❌ Errors: {errors}")
    print("\nNext: Update data quality scores:")
    print("  SELECT update_all_vendor_data_quality_scores();")


if __name__ == "__main__":
    update_vendors()
