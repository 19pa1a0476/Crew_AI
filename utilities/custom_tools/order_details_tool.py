import pandas as pd
import json
import gc
from typing import List, Dict, Optional
from agno.tools import Toolkit


class OrderDetailsTools(Toolkit):
    def __init__(self, **kwargs):
        super().__init__(name="Order Details Tool", 
                        tools=[self.get_order_details, self.get_orders_by_seller],
                        **kwargs)
    
    def get_order_details(self, order_id: Optional[str] = None, customer_name: Optional[str] = None) -> Dict:
        """
        Returns detailed information about agricultural orders from the SAP system.
        
        Args:
            order_id (Optional[str]): Filter by specific order ID (e.g., '4500024312')
            customer_name (Optional[str]): Filter by customer name (e.g., 'Green Valley Farms Inc.')
            
        Returns:
            Dict: Order details in JSON format, or all orders if no filter is specified
        """
        try:
            # Sample agricultural order data - hardcoded for demonstration
            orders_data = [
                {
                    "orderHeader": {
                        "salesOrderId": "4500023871",
                        "sapDocumentNumber": "2000567324",
                        "creationDate": "2025-05-15T09:23:45Z",
                        "orderStatus": "CONFIRMED",
                        "orderType": "AGRI",
                        "distributionChannel": "10",
                        "salesOrganization": "US01",
                        "totalValue": 24583.50,
                        "currency": "USD"
                    },
                    "customer": {
                        "customerId": "2200034567",
                        "customerName": "Green Valley Farms Inc.",
                        "customerType": "FARMER",
                        "customerCategory": "PREMIUM",
                        "region": "MIDWEST"
                    },
                    "orderItems": [
                        {
                            "itemNumber": "10",
                            "materialNumber": "FERT-1045-20",
                            "materialDescription": "Premium NPK Fertilizer 10-45-20",
                            "quantity": 120,
                            "uom": "BAG",
                            "unitPrice": 67.50,
                            "netValue": 8100.00
                        },
                        {
                            "itemNumber": "20",
                            "materialNumber": "SEED-CO-RR4521",
                            "materialDescription": "Round-Up Ready Corn Seed XR4521",
                            "quantity": 45,
                            "uom": "UNIT",
                            "unitPrice": 245.00,
                            "netValue": 11025.00
                        }
                    ],
                    "salesRepresentative": {
                        "employeeId": "E000123",
                        "name": "Michael Peterson",
                        "region": "MIDWEST",
                        "salesTeam": "FIELD CROPS",
                        "totalSalesYTD": 1245600.00
                    }
                },
                {
                    "orderHeader": {
                        "salesOrderId": "4500023886",
                        "sapDocumentNumber": "2000567340",
                        "creationDate": "2025-05-16T10:45:12Z",
                        "orderStatus": "PROCESSING",
                        "orderType": "AGRI",
                        "distributionChannel": "10",
                        "salesOrganization": "US01",
                        "totalValue": 13650.75,
                        "currency": "USD"
                    },
                    "customer": {
                        "customerId": "2200034582",
                        "customerName": "Harvest Moon Organics LLC",
                        "customerType": "ORGANIC FARMER",
                        "customerCategory": "STANDARD",
                        "region": "MIDWEST"
                    },
                    "orderItems": [
                        {
                            "itemNumber": "10",
                            "materialNumber": "FERT-ORG-5040",
                            "materialDescription": "Organic Compost Premium Blend",
                            "quantity": 85,
                            "uom": "BAG",
                            "unitPrice": 84.75,
                            "netValue": 7203.75
                        },
                        {
                            "itemNumber": "20",
                            "materialNumber": "SEED-ORG-TOM12",
                            "materialDescription": "Organic Heirloom Tomato Seeds Mix",
                            "quantity": 50,
                            "uom": "PACK",
                            "unitPrice": 128.94,
                            "netValue": 6447.00
                        }
                    ],
                    "salesRepresentative": {
                        "employeeId": "E000123",
                        "name": "Michael Peterson",
                        "region": "MIDWEST",
                        "salesTeam": "FIELD CROPS",
                        "totalSalesYTD": 1245600.00
                    }
                },
                {
                    "orderHeader": {
                        "salesOrderId": "4500024012",
                        "sapDocumentNumber": "2000567498",
                        "creationDate": "2025-05-17T14:23:10Z",
                        "orderStatus": "CONFIRMED",
                        "orderType": "AGRI",
                        "distributionChannel": "10",
                        "salesOrganization": "US01",
                        "totalValue": 35792.40,
                        "currency": "USD"
                    },
                    "customer": {
                        "customerId": "2200038765",
                        "customerName": "California Sunshine Vineyards",
                        "customerType": "VINEYARD",
                        "customerCategory": "PREMIUM",
                        "region": "WEST"
                    },
                    "orderItems": [
                        {
                            "itemNumber": "10",
                            "materialNumber": "PEST-FUN-VIN10",
                            "materialDescription": "Premium Vineyard Fungicide",
                            "quantity": 60,
                            "uom": "DRUM",
                            "unitPrice": 345.99,
                            "netValue": 20759.40
                        },
                        {
                            "itemNumber": "20",
                            "materialNumber": "IRRIG-DRP-50MM",
                            "materialDescription": "Drip Irrigation System Components",
                            "quantity": 150,
                            "uom": "ROLL",
                            "unitPrice": 100.22,
                            "netValue": 15033.00
                        }
                    ],
                    "salesRepresentative": {
                        "employeeId": "E000456",
                        "name": "Sarah Williams",
                        "region": "WEST",
                        "salesTeam": "SPECIALTY CROPS",
                        "totalSalesYTD": 1678300.00
                    }
                },
                {
                    "orderHeader": {
                        "salesOrderId": "4500024033",
                        "sapDocumentNumber": "2000567545",
                        "creationDate": "2025-05-18T08:34:56Z",
                        "orderStatus": "CONFIRMED",
                        "orderType": "AGRI",
                        "distributionChannel": "10",
                        "salesOrganization": "US01",
                        "totalValue": 42105.25,
                        "currency": "USD"
                    },
                    "customer": {
                        "customerId": "2200039023",
                        "customerName": "Pacific Almond Growers",
                        "customerType": "ORCHARD",
                        "customerCategory": "PREMIUM",
                        "region": "WEST"
                    },
                    "orderItems": [
                        {
                            "itemNumber": "10",
                            "materialNumber": "FERT-TREE-SPNP",
                            "materialDescription": "Slow-Release Nut Tree Fertilizer",
                            "quantity": 230,
                            "uom": "BAG",
                            "unitPrice": 127.45,
                            "netValue": 29313.50
                        },
                        {
                            "itemNumber": "20",
                            "materialNumber": "PEST-INS-12500",
                            "materialDescription": "Orchard Insect Control Solution",
                            "quantity": 85,
                            "uom": "CANISTER",
                            "unitPrice": 150.49,
                            "netValue": 12791.75
                        }
                    ],
                    "salesRepresentative": {
                        "employeeId": "E000456",
                        "name": "Sarah Williams",
                        "region": "WEST",
                        "salesTeam": "SPECIALTY CROPS",
                        "totalSalesYTD": 1678300.00
                    }
                },
                {
                    "orderHeader": {
                        "salesOrderId": "4500024156",
                        "sapDocumentNumber": "2000567678",
                        "creationDate": "2025-05-18T11:28:32Z",
                        "orderStatus": "PROCESSING",
                        "orderType": "AGRI",
                        "distributionChannel": "10",
                        "salesOrganization": "US01",
                        "totalValue": 54287.65,
                        "currency": "USD"
                    },
                    "customer": {
                        "customerId": "2200041278",
                        "customerName": "Southern Cotton Enterprises",
                        "customerType": "COTTON PRODUCER",
                        "customerCategory": "PREMIUM",
                        "region": "SOUTH"
                    },
                    "orderItems": [
                        {
                            "itemNumber": "10",
                            "materialNumber": "SEED-COT-BG455",
                            "materialDescription": "BollGard Cotton Seed Premium",
                            "quantity": 180,
                            "uom": "BAG",
                            "unitPrice": 195.75,
                            "netValue": 35235.00
                        },
                        {
                            "itemNumber": "20",
                            "materialNumber": "SOIL-ENH-COT20",
                            "materialDescription": "Cotton Soil Enhancement Treatment",
                            "quantity": 120,
                            "uom": "DRUM",
                            "unitPrice": 158.77,
                            "netValue": 19052.65
                        }
                    ],
                    "salesRepresentative": {
                        "employeeId": "E000789",
                        "name": "Tyrone Jackson",
                        "region": "SOUTH",
                        "salesTeam": "COTTON & FIBER",
                        "totalSalesYTD": 2134500.00
                    }
                },
                {
                    "orderHeader": {
                        "salesOrderId": "4500024198",
                        "sapDocumentNumber": "2000567704",
                        "creationDate": "2025-05-19T09:12:48Z",
                        "orderStatus": "CONFIRMED",
                        "orderType": "AGRI",
                        "distributionChannel": "10",
                        "salesOrganization": "US01",
                        "totalValue": 31245.20,
                        "currency": "USD"
                    },
                    "customer": {
                        "customerId": "2200042103",
                        "customerName": "Delta Rice Farms Inc.",
                        "customerType": "RICE PRODUCER",
                        "customerCategory": "STANDARD",
                        "region": "SOUTH"
                    },
                    "orderItems": [
                        {
                            "itemNumber": "10",
                            "materialNumber": "FERT-RICE-1020",
                            "materialDescription": "Rice Field Fertilizer Blend",
                            "quantity": 200,
                            "uom": "BAG",
                            "unitPrice": 89.95,
                            "netValue": 17990.00
                        },
                        {
                            "itemNumber": "20",
                            "materialNumber": "HERB-RICE-5000",
                            "materialDescription": "Rice Weed Control Solution",
                            "quantity": 65,
                            "uom": "CONTAINER",
                            "unitPrice": 204.08,
                            "netValue": 13265.20
                        }
                    ],
                    "salesRepresentative": {
                        "employeeId": "E000789",
                        "name": "Tyrone Jackson",
                        "region": "SOUTH",
                        "salesTeam": "COTTON & FIBER",
                        "totalSalesYTD": 2134500.00
                    }
                },
                {
                    "orderHeader": {
                        "salesOrderId": "4500024217",
                        "sapDocumentNumber": "2000567798",
                        "creationDate": "2025-05-19T14:45:21Z",
                        "orderStatus": "PROCESSING",
                        "orderType": "AGRI",
                        "distributionChannel": "10",
                        "salesOrganization": "US01",
                        "totalValue": 28456.80,
                        "currency": "USD"
                    },
                    "customer": {
                        "customerId": "2200045670",
                        "customerName": "North East Dairy Cooperative",
                        "customerType": "DAIRY",
                        "customerCategory": "PREMIUM",
                        "region": "NORTHEAST"
                    },
                    "orderItems": [
                        {
                            "itemNumber": "10",
                            "materialNumber": "SEED-ALF-PRO45",
                            "materialDescription": "Premium Alfalfa Seed Mix",
                            "quantity": 85,
                            "uom": "BAG",
                            "unitPrice": 187.40,
                            "netValue": 15929.00
                        },
                        {
                            "itemNumber": "20",
                            "materialNumber": "FEED-SUP-DAIRY",
                            "materialDescription": "High-Protein Dairy Feed Supplement",
                            "quantity": 125,
                            "uom": "BAG",
                            "unitPrice": 100.22,
                            "netValue": 12527.80
                        }
                    ],
                    "salesRepresentative": {
                        "employeeId": "E000321",
                        "name": "Jennifer Connelly",
                        "region": "NORTHEAST",
                        "salesTeam": "DAIRY & LIVESTOCK",
                        "totalSalesYTD": 1845200.00
                    }
                },
                {
                    "orderHeader": {
                        "salesOrderId": "4500024256",
                        "sapDocumentNumber": "2000567834",
                        "creationDate": "2025-05-20T08:56:34Z",
                        "orderStatus": "CONFIRMED",
                        "orderType": "AGRI",
                        "distributionChannel": "10",
                        "salesOrganization": "US01",
                        "totalValue": 41578.95,
                        "currency": "USD"
                    },
                    "customer": {
                        "customerId": "2200046892",
                        "customerName": "Hudson Valley Orchards",
                        "customerType": "ORCHARD",
                        "customerCategory": "PREMIUM",
                        "region": "NORTHEAST"
                    },
                    "orderItems": [
                        {
                            "itemNumber": "10",
                            "materialNumber": "PEST-ORCH-PRO10",
                            "materialDescription": "Apple Orchard Pest Management System",
                            "quantity": 45,
                            "uom": "KIT",
                            "unitPrice": 458.75,
                            "netValue": 20643.75
                        },
                        {
                            "itemNumber": "20",
                            "materialNumber": "FERT-FRUIT-15KG",
                            "materialDescription": "Fruit Tree Specialized Fertilizer",
                            "quantity": 210,
                            "uom": "BAG",
                            "unitPrice": 99.69,
                            "netValue": 20935.20
                        }
                    ],
                    "salesRepresentative": {
                        "employeeId": "E000321",
                        "name": "Jennifer Connelly",
                        "region": "NORTHEAST",
                        "salesTeam": "DAIRY & LIVESTOCK",
                        "totalSalesYTD": 1845200.00
                    }
                },
                {
                    "orderHeader": {
                        "salesOrderId": "4500024312",
                        "sapDocumentNumber": "2000567901",
                        "creationDate": "2025-05-20T10:23:54Z",
                        "orderStatus": "PROCESSING",
                        "orderType": "AGRI",
                        "distributionChannel": "10",
                        "salesOrganization": "US01",
                        "totalValue": 18945.60,
                        "currency": "USD"
                    },
                    "customer": {
                        "customerId": "2200049756",
                        "customerName": "Prairie Wind Grains LLC",
                        "customerType": "GRAIN PRODUCER",
                        "customerCategory": "STANDARD",
                        "region": "CENTRAL"
                    },
                    "orderItems": [
                        {
                            "itemNumber": "10",
                            "materialNumber": "SEED-WHT-HR452",
                            "materialDescription": "Hard Red Spring Wheat Seed",
                            "quantity": 120,
                            "uom": "BAG",
                            "unitPrice": 105.38,
                            "netValue": 12645.60
                        },
                        {
                            "itemNumber": "20",
                            "materialNumber": "SOIL-TEST-KIT-PRO",
                            "materialDescription": "Professional Soil Testing Kit",
                            "quantity": 21,
                            "uom": "KIT",
                            "unitPrice": 300.00,
                            "netValue": 6300.00
                        }
                    ],
                    "salesRepresentative": {
                        "employeeId": "E000567",
                        "name": "Robert Chen",
                        "region": "CENTRAL",
                        "salesTeam": "GRAIN & CEREALS",
                        "totalSalesYTD": 1564300.00
                    }
                },
                {
                    "orderHeader": {
                        "salesOrderId": "4500024356",
                        "sapDocumentNumber": "2000567945",
                        "creationDate": "2025-05-20T13:42:18Z",
                        "orderStatus": "CONFIRMED",
                        "orderType": "AGRI",
                        "distributionChannel": "10",
                        "salesOrganization": "US01",
                        "totalValue": 45678.90,
                        "currency": "USD"
                    },
                    "customer": {
                        "customerId": "2200051234",
                        "customerName": "Great Plains Soy Producers",
                        "customerType": "SOY PRODUCER",
                        "customerCategory": "PREMIUM",
                        "region": "CENTRAL"
                    },
                    "orderItems": [
                        {
                            "itemNumber": "10",
                            "materialNumber": "SEED-SOY-RR789",
                            "materialDescription": "Roundup Ready Soybean Seed Premium",
                            "quantity": 150,
                            "uom": "BAG",
                            "unitPrice": 215.89,
                            "netValue": 32383.50
                        },
                        {
                            "itemNumber": "20",
                            "materialNumber": "FERT-SOY-MICRO",
                            "materialDescription": "Soybean Micronutrient Formula",
                            "quantity": 110,
                            "uom": "CONTAINER",
                            "unitPrice": 120.87,
                            "netValue": 13295.40
                        }
                    ],
                    "salesRepresentative": {
                        "employeeId": "E000567",
                        "name": "Robert Chen",
                        "region": "CENTRAL",
                        "salesTeam": "GRAIN & CEREALS",
                        "totalSalesYTD": 1564300.00
                    }
                }
            ]
            
            # Apply filters if provided
            if order_id:
                filtered_orders = [order for order in orders_data if order["orderHeader"]["salesOrderId"] == order_id]
                return filtered_orders[0] if filtered_orders else {"error": f"No order found with ID: {order_id}"}
            
            if customer_name:
                filtered_orders = [order for order in orders_data if order["customer"]["customerName"] == customer_name]
                return filtered_orders if filtered_orders else {"error": f"No orders found for customer: {customer_name}"}
            
            # Return all orders if no filter is specified
            return orders_data
            
        except Exception as e:
            print(f"Error occurred: {e}")
            return {"error": str(e)}
            
        finally:
            gc.collect()
    
    def get_orders_by_seller(self, employee_id: Optional[str] = None, sales_rep_name: Optional[str] = None, region: Optional[str] = None) -> List[Dict]:
        """
        Returns orders filtered by sales representative criteria.
        
        Args:
            employee_id (Optional[str]): Filter by employee ID (e.g., 'E000123')
            sales_rep_name (Optional[str]): Filter by sales representative name (e.g., 'Michael Peterson')
            region (Optional[str]): Filter by region (e.g., 'MIDWEST', 'WEST', 'SOUTH', 'NORTHEAST', 'CENTRAL')
            
        Returns:
            List[Dict]: List of orders matching the specified criteria
        """
        try:
            # Get all orders first
            all_orders = self.get_order_details()
            
            # Apply filters based on sales representative criteria
            if employee_id:
                return [order for order in all_orders if order["salesRepresentative"]["employeeId"] == employee_id]
            
            if sales_rep_name:
                return [order for order in all_orders if order["salesRepresentative"]["name"] == sales_rep_name]
            
            if region:
                return [order for order in all_orders if order["salesRepresentative"]["region"] == region.upper()]
            
            # Return all orders if no filter is specified
            return all_orders
            
        except Exception as e:
            print(f"Error occurred: {e}")
            return [{"error": str(e)}]
            
        finally:
            gc.collect()



# if __name__ == "__main__":
#     # Initialize the tool
#     agri_tools = OrderDetailsTools()
    
#     # Example 1: Get all orders
#     all_orders = agri_tools.get_order_details()
#     print(f"Total orders: {len(all_orders)}")
    
#     # Example 2: Filter by order ID
#     order = agri_tools.get_order_details(order_id="4500024156")
#     print(f"Order for Southern Cotton Enterprises: {order['customer']['customerName']}")
    
#     # Example 3: Get orders by sales representative
#     midwest_orders = agri_tools.get_orders_by_seller(region="MIDWEST")
#     print(f"Orders from Midwest region: {len(midwest_orders)}")