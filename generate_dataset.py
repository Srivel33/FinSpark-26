import os
import random
import uuid
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# ====================================================================
# CONFIGURATION & CONSTANTS
# ====================================================================

class Config:
    NUM_CUSTOMERS = 50
    NUM_TRANSACTIONS = 1000
    OUTPUT_DIR = "output"
    FRAUD_RATIO = 0.12  # 12% fraud rate
    
    INDIAN_CITIES = [
        "Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai", 
        "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow", 
        "Chandigarh", "Indore", "Coimbatore", "Kochi", "Gurgaon"
    ]
    
    INDIAN_STATES = {
        "Mumbai": "Maharashtra", "Delhi": "Delhi", "Bengaluru": "Karnataka",
        "Hyderabad": "Telangana", "Chennai": "Tamil Nadu", "Kolkata": "West Bengal",
        "Pune": "Maharashtra", "Ahmedabad": "Gujarat", "Jaipur": "Rajasthan",
        "Lucknow": "Uttar Pradesh", "Chandigarh": "Punjab", "Indore": "Madhya Pradesh",
        "Coimbatore": "Tamil Nadu", "Kochi": "Kerala", "Gurgaon": "Haryana"
    }
    
    BANKS = ["HDFC Bank", "SBI", "ICICI Bank", "Axis Bank", "Kotak Mahindra", "PNB", "Yes Bank"]
    
    MERCHANTS = [
        {"name": "Amazon India", "category": "E-commerce", "high_risk": False},
        {"name": "Flipkart", "category": "E-commerce", "high_risk": False},
        {"name": "Zomato", "category": "Food", "high_risk": False},
        {"name": "Swiggy", "category": "Food", "high_risk": False},
        {"name": "Reliance Smart", "category": "Groceries", "high_risk": False},
        {"name": "D-Mart", "category": "Groceries", "high_risk": False},
        {"name": "MakeMyTrip", "category": "Travel", "high_risk": False},
        {"name": "Cleartrip", "category": "Travel", "high_risk": False},
        {"name": "Binance", "category": "Crypto", "high_risk": True},
        {"name": "WazirX", "category": "Crypto", "high_risk": True},
        {"name": "Local Kirana", "category": "Retail", "high_risk": False},
        {"name": "Croma", "category": "Electronics", "high_risk": False},
        {"name": "Offshore Bet", "category": "Gaming", "high_risk": True},
        {"name": "Western Union", "category": "Remittance", "high_risk": True}
    ]
    
    PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Net Banking", "IMPS", "NEFT"]
    DEVICE_TYPES = ["Smartphone", "Laptop", "Desktop", "Tablet"]
    BROWSERS = ["Chrome", "Safari", "Firefox", "Edge", "Mobile App"]
    OS = ["Android", "iOS", "Windows", "macOS"]
    
    FIRST_NAMES = [
        "Aarav", "Vihaan", "Aditya", "Sai", "Arjun", "Rohan", "Vikram", "Rahul", "Amit", "Karan", 
        "Diya", "Isha", "Riya", "Ananya", "Kavya", "Neha", "Priya", "Sneha", "Pooja", "Meera",
        "Rajesh", "Suresh", "Ramesh", "Mahesh", "Gita", "Sita", "Anita", "Sunita"
    ]
    
    LAST_NAMES = [
        "Sharma", "Verma", "Patel", "Singh", "Kumar", "Gupta", "Reddy", "Rao", "Nair", "Menon", 
        "Iyer", "Joshi", "Desai", "Jain", "Bose", "Chatterjee", "Sengupta", "Yadav", "Chauhan"
    ]

# ====================================================================
# UTILITY FUNCTIONS
# ====================================================================

class Utils:
    @staticmethod
    def generate_id(prefix=""):
        return f"{prefix}{uuid.uuid4().hex[:12].upper()}"
    
    @staticmethod
    def random_ip():
        return f"{random.randint(11, 250)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
    
    @staticmethod
    def generate_name():
        return f"{random.choice(Config.FIRST_NAMES)} {random.choice(Config.LAST_NAMES)}"

    @staticmethod
    def get_natural_failed_logins(is_fraud, scenario=""):
        if is_fraud and scenario == "CREDENTIAL_STUFFING":
            # Credential stuffing yields highly unnatural login failures
            return random.choices([4, 5, 6, 7, 8], weights=[10, 20, 30, 20, 20], k=1)[0]
        elif is_fraud and scenario == "ACCOUNT_TAKEOVER":
            return random.choices([2, 3, 4, 5], weights=[25, 40, 25, 10], k=1)[0]
        else:
            # Normal users mostly get it right, sometimes make a typo
            return random.choices([0, 1, 2, 3, 4], weights=[85, 10, 4, 0.8, 0.2], k=1)[0]

# ====================================================================
# DATA GENERATOR
# ====================================================================

class DataGenerator:
    def __init__(self):
        # Set seeds for reproducible execution
        random.seed(42)
        np.random.seed(42)
        
        self.customers = []
        self.transactions = []
        self.security_logs = []
        
        # State tracking for realistic behavior progression
        self.customer_state = {}
        self.receivers_db = {}  # receiver_account -> dict with name, bank, trust_score, risk_score
        
    def generate_customers(self):
        personas = [
            {"type": "Student", "age_range": (18, 23), "income": (50000, 200000), "avg_txn": (150, 800)},
            {"type": "Salaried", "age_range": (24, 55), "income": (400000, 2500000), "avg_txn": (800, 5000)},
            {"type": "Business", "age_range": (30, 60), "income": (2000000, 15000000), "avg_txn": (10000, 80000)},
            {"type": "Senior Citizen", "age_range": (61, 80), "income": (200000, 1000000), "avg_txn": (500, 3000)}
        ]
        
        for _ in range(Config.NUM_CUSTOMERS):
            persona = random.choice(personas)
            city = random.choice(Config.INDIAN_CITIES)
            customer_id = Utils.generate_id("CUST_")
            
            self.customers.append({
                "customer_id": customer_id,
                "customer_name": Utils.generate_name(),
                "account_number": f"AC{random.randint(100000000, 999999999)}",
                "account_type": random.choice(["Savings", "Current", "Salary"]),
                "persona": persona["type"],
                "age": random.randint(*persona["age_range"]),
                "gender": random.choice(["Male", "Female"]),
                "occupation": persona["type"],
                "annual_income": random.randint(*persona["income"]),
                "home_city": city,
                "home_state": Config.INDIAN_STATES[city],
                "home_country": "India",
                "registered_device_id": Utils.generate_id("DEV_"),
                "registered_device_type": random.choice(Config.DEVICE_TYPES),
                "preferred_payment_method": random.choice(Config.PAYMENT_METHODS),
                "average_transaction_amount": round(random.uniform(*persona["avg_txn"]), 2),
                "account_age_days": random.randint(30, 3650),
                "kyc_status": random.choices(["Verified", "Pending"], weights=[95, 5], k=1)[0],
                "trusted_ip": Utils.random_ip(),
                "trusted_ip_reputation": random.randint(85, 100)
            })
            
            # Initialize behavioral state
            self.customer_state[customer_id] = {
                "current_city": city,
                "last_login_city": city,
                "last_login_time": datetime.now() - timedelta(days=60),
                "known_receivers": set(),
                "is_travelling": False,
                "travel_end_time": None
            }

    def _get_receiver(self, customer_id, force_new=False, force_high_risk=False):
        state = self.customer_state[customer_id]
        
        # 80% chance to reuse known receiver if available and not forcing new
        if not force_new and len(state["known_receivers"]) > 0 and random.random() < 0.8:
            recv_acc = random.choice(list(state["known_receivers"]))
            recv_info = self.receivers_db[recv_acc]
            is_new = False
        else:
            # Generate new receiver
            recv_acc = f"REC_AC{random.randint(100000, 999999)}"
            
            if force_high_risk:
                trust = random.randint(5, 30)
                risk = random.randint(70, 95)
            else:
                trust = random.randint(70, 100)
                risk = random.randint(0, 30)
                
            recv_info = {
                "name": Utils.generate_name(),
                "bank": random.choice(Config.BANKS),
                "trust_score": trust,
                "risk_score": risk
            }
            self.receivers_db[recv_acc] = recv_info
            
            if not force_high_risk:  # Don't add fraud accounts to known list
                state["known_receivers"].add(recv_acc)
            is_new = True
            
        return recv_acc, recv_info, is_new

    def generate_events(self):
        # Generate chronologically to maintain state logic
        start_time = datetime.now() - timedelta(days=30)
        current_time = start_time
        
        for _ in range(Config.NUM_TRANSACTIONS):
            # Advance time by 1 to 60 minutes randomly
            current_time += timedelta(minutes=random.randint(1, 60))
            
            # Select random customer
            cust = random.choice(self.customers)
            cust_id = cust["customer_id"]
            state = self.customer_state[cust_id]
            
            # Check travel state expiration
            if state["is_travelling"] and state["travel_end_time"] and current_time > state["travel_end_time"]:
                state["is_travelling"] = False
                state["current_city"] = cust["home_city"]
            
            # Legit users occasionally start travelling (Location variation)
            if not state["is_travelling"] and random.random() < 0.05:
                state["is_travelling"] = True
                travel_cities = [c for c in Config.INDIAN_CITIES if c != cust["home_city"]]
                state["current_city"] = random.choice(travel_cities)
                state["travel_end_time"] = current_time + timedelta(days=random.randint(1, 5))
            
            is_fraud = random.random() < Config.FRAUD_RATIO
            scenario = ""
            
            # --- DEFAULT NORMAL BEHAVIOUR ---
            merchant = random.choices(
                population=Config.MERCHANTS,
                weights=[80 if not m["high_risk"] else 5 for m in Config.MERCHANTS],
                k=1
            )[0]
            
            # Normal amount varies safely around the customer's average
            if random.random() < 0.05: # Occasional legit high value (e.g. buying TV, rent)
                amount = round(cust["average_transaction_amount"] * random.uniform(3, 5), 2)
            else:
                amount = round(cust["average_transaction_amount"] * random.uniform(0.3, 1.5), 2)
                
            txn_city = state["current_city"]
            login_city = state["current_city"] 
            dev_id = cust["registered_device_id"]
            dev_type = cust["registered_device_type"]
            ip = cust["trusted_ip"] if not state["is_travelling"] else Utils.random_ip()
            vpn = True if random.random() < 0.05 else False # Normal users use VPN sometimes
            pwd_reset = False
            failed_log = Utils.get_natural_failed_logins(False)
            recv_acc, recv_info, is_new_recv = self._get_receiver(cust_id, force_new=(random.random() < 0.1))
            ip_rep = random.randint(85, 100) if not vpn else random.randint(50, 80)
            otp_verified = True if random.random() < 0.98 else False # Normal rarely fails OTP
            
            # --- APPLY FRAUD SCENARIOS OVERRIDES ---
            if is_fraud:
                scenario = random.choice([
                    "ACCOUNT_TAKEOVER", 
                    "CREDENTIAL_STUFFING", 
                    "IMPOSSIBLE_TRAVEL", 
                    "NEW_DEVICE_VPN", 
                    "HIGH_VELOCITY", 
                    "CRYPTO_ABUSE"
                ])
                
                if scenario == "ACCOUNT_TAKEOVER":
                    dev_id = Utils.generate_id("DEV_")
                    ip = Utils.random_ip()
                    pwd_reset = True
                    failed_log = Utils.get_natural_failed_logins(True, scenario)
                    amount = round(cust["average_transaction_amount"] * random.uniform(5, 15), 2)
                    ip_rep = random.randint(10, 40)
                    recv_acc, recv_info, is_new_recv = self._get_receiver(cust_id, force_new=True, force_high_risk=True)
                    login_city = random.choice(Config.INDIAN_CITIES)
                    txn_city = login_city
                    
                elif scenario == "CREDENTIAL_STUFFING":
                    failed_log = Utils.get_natural_failed_logins(True, scenario)
                    ip = Utils.random_ip()
                    vpn = True
                    ip_rep = random.randint(5, 25)
                    dev_id = Utils.generate_id("DEV_")
                    otp_verified = False # Attacker doesn't have the phone
                    
                elif scenario == "IMPOSSIBLE_TRAVEL":
                    # Attacker logs in from a completely different city immediately after the legit user
                    login_city = "Delhi" if state["last_login_city"] != "Delhi" else "Chennai"
                    txn_city = login_city
                    ip = Utils.random_ip()
                    # We force the event time to be just 5 minutes after the last login
                    current_time = state["last_login_time"] + timedelta(minutes=5)
                    amount = round(cust["average_transaction_amount"] * random.uniform(2, 6), 2)
                    
                elif scenario == "NEW_DEVICE_VPN":
                    dev_id = Utils.generate_id("DEV_")
                    vpn = True
                    ip = Utils.random_ip()
                    ip_rep = random.randint(30, 60)
                    amount = round(cust["average_transaction_amount"] * random.uniform(4, 8), 2)
                    recv_acc, recv_info, is_new_recv = self._get_receiver(cust_id, force_new=True, force_high_risk=True)
                    
                elif scenario == "CRYPTO_ABUSE":
                    merchant = next(m for m in Config.MERCHANTS if m["category"] == "Crypto")
                    vpn = True
                    amount = round(cust["average_transaction_amount"] * random.uniform(8, 20), 2)
                    recv_acc, recv_info, is_new_recv = self._get_receiver(cust_id, force_new=True, force_high_risk=True)
                    
                elif scenario == "HIGH_VELOCITY":
                    dev_id = Utils.generate_id("DEV_")
                    # Time artificially close to last event
                    current_time = state["last_login_time"] + timedelta(seconds=random.randint(30, 120))
                    amount = round(cust["average_transaction_amount"] * random.uniform(1, 3), 2)
                    recv_acc, recv_info, is_new_recv = self._get_receiver(cust_id, force_new=True)

            # Sometimes the transaction gateway registers a different location than the login IP
            # e.g., using a payment gateway routed through Mumbai while logged in from Pune
            if not is_fraud and random.random() < 0.1:
                txn_city = random.choice([c for c in Config.INDIAN_CITIES if c != login_city])

            txn_id = Utils.generate_id("TXN_")
            log_id = Utils.generate_id("LOG_")
            
            # Formulate timing
            login_time = current_time - timedelta(minutes=random.randint(1, 15))
            logout_time = current_time + timedelta(minutes=random.randint(1, 20))
            session_dur = int((logout_time - login_time).total_seconds() / 60)

            # --- APPEND TRANSACTION RECORD ---
            self.transactions.append({
                "transaction_id": txn_id,
                "customer_id": cust_id,
                "sender_account": cust["account_number"],
                "receiver_account": recv_acc,
                "receiver_name": recv_info["name"],
                "receiver_bank": recv_info["bank"],
                "merchant_category": merchant["category"],
                "merchant_name": merchant["name"],
                "amount": amount,
                "payment_method": cust["preferred_payment_method"] if not is_fraud else random.choice(Config.PAYMENT_METHODS),
                "transaction_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "transaction_location": txn_city,
                "transaction_country": "India",
                "transaction_status": "Success" if otp_verified else "Failed",
                "currency": "INR",
                
                # Hidden ground truth logic passing to Feature Engineer
                "_is_fraud": 1 if is_fraud else 0,
                "_is_new_receiver": 1 if is_new_recv else 0,
                "_receiver_trust_score": recv_info["trust_score"],
                "_receiver_risk_score": recv_info["risk_score"]
            })
            
            # --- APPEND CYBERSECURITY RECORD ---
            self.security_logs.append({
                "log_id": log_id,
                "transaction_id": txn_id,
                "customer_id": cust_id,
                "login_time": login_time.strftime("%Y-%m-%d %H:%M:%S"),
                "logout_time": logout_time.strftime("%Y-%m-%d %H:%M:%S"),
                "event_type": "Transaction_Initiated",
                "login_location": login_city,
                "previous_login_city": state["last_login_city"],
                "device_id": dev_id,
                "device_type": dev_type,
                "browser": random.choice(Config.BROWSERS),
                "operating_system": random.choice(Config.OS),
                "ip_address": ip,
                "vpn_used": vpn,
                "failed_login_count": failed_log,
                "password_reset": pwd_reset,
                "otp_verified": otp_verified,
                "session_duration_minutes": session_dur,
                "ip_reputation_score": ip_rep,
                "login_method": random.choices(["Password", "Biometric", "PIN"], weights=[60, 30, 10], k=1)[0],
                "biometric_used": random.choice([True, False]),
                "country": "India"
            })
            
            # Update customer state for the next iteration
            state["last_login_city"] = login_city
            state["last_login_time"] = login_time

# ====================================================================
# FEATURE ENGINEERING & CORRELATION
# ====================================================================

class FeatureEngineer:
    @staticmethod
    def correlate_datasets(cust_df, txn_df, sec_df):
        # Secure the ground truth attributes before merging
        ground_truth = txn_df[['transaction_id', '_is_fraud', '_is_new_receiver', '_receiver_trust_score', '_receiver_risk_score']].copy()
        txn_clean = txn_df.drop(columns=['_is_fraud', '_is_new_receiver', '_receiver_trust_score', '_receiver_risk_score'])
        
        # 1. Merge all datasets structurally mimicking the AI Correlation Engine
        df = txn_clean.merge(sec_df, on=["transaction_id", "customer_id"], how="inner")
        df = df.merge(cust_df, on="customer_id", how="inner")
        df = df.merge(ground_truth, on="transaction_id", how="inner")
        
        # 2. Convert timestamps for chronological processing
        df["transaction_time"] = pd.to_datetime(df["transaction_time"])
        df["login_time"] = pd.to_datetime(df["login_time"])
        
        # Sort values explicitly to guarantee temporal calculations are correct
        df = df.sort_values(by=["customer_id", "transaction_time"]).reset_index(drop=True)
        
        ml_dataset = []
        
        # 3. Iterate through rows to safely construct features including historical rolling windows
        for idx, row in df.iterrows():
            cust_id = row["customer_id"]
            curr_time = row["transaction_time"]
            
            past_1h_count = 0
            past_24h_count = 0
            
            # Backtrack to find past transactions for the same customer
            for j in range(idx - 1, -1, -1):
                past_row = df.iloc[j]
                if past_row["customer_id"] != cust_id:
                    break
                    
                time_diff_sec = (curr_time - past_row["transaction_time"]).total_seconds()
                
                if time_diff_sec <= 3600:
                    past_1h_count += 1
                if time_diff_sec <= 86400:
                    past_24h_count += 1
                else:
                    break # Optimization: If we cross 24h, stop backtracking
                    
            amount = float(row["amount"])
            avg_txn = float(row["average_transaction_amount"])
            time_gap = (curr_time - row["login_time"]).total_seconds() / 60.0
            
            # Impossible travel calculation: location change + unrealistic time frame (< 2 hours)
            impossible_travel = 1 if (row["previous_login_city"] != row["login_location"] and time_gap < 120) else 0

            # Construct the final ML-Ready Row explicitly as required
            ml_row = {
                "amount": amount,
                "average_transaction_amount": avg_txn,
                "amount_ratio": round(amount / avg_txn, 3) if avg_txn > 0 else 0.0,
                "transaction_hour": curr_time.hour,
                "transaction_day": curr_time.weekday(),
                "location_match": 1 if row["transaction_location"] == row["login_location"] else 0,
                "location_changed": 1 if row["transaction_location"] != row["home_city"] else 0,
                "new_device": 1 if row["device_id"] != row["registered_device_id"] else 0,
                "trusted_ip": 1 if row["ip_address"] == row["trusted_ip"] else 0,
                "vpn_used": 1 if row["vpn_used"] else 0,
                "failed_login_count": row["failed_login_count"],
                "password_reset": 1 if row["password_reset"] else 0,
                "otp_verified": 1 if row["otp_verified"] else 0,
                "session_duration_minutes": row["session_duration_minutes"],
                "ip_reputation_score": row["ip_reputation_score"],
                "new_receiver": row["_is_new_receiver"],
                "receiver_trust_score": row["_receiver_trust_score"],
                "receiver_risk_score": row["_receiver_risk_score"],
                "merchant_category": row["merchant_category"],
                "payment_method": row["payment_method"],
                "high_risk_merchant": 1 if row["merchant_category"] in ["Crypto", "Gaming", "Remittance"] else 0,
                "night_transaction": 1 if (curr_time.hour < 5 or curr_time.hour > 23) else 0,
                "impossible_travel": impossible_travel,
                "time_gap_minutes": round(max(0, time_gap), 2),
                "previous_transactions_last_1_hour": past_1h_count,
                "previous_transactions_last_24_hours": past_24h_count,
                "high_value_transaction": 1 if amount > (avg_txn * 4) else 0,
                "persona": row["persona"],
                "home_city": row["home_city"],
                "login_city": row["login_location"],
                "transaction_city": row["transaction_location"],
                "is_fraud": row["_is_fraud"]
            }
            ml_dataset.append(ml_row)
            
        return pd.DataFrame(ml_dataset)

# ====================================================================
# PIPELINE EXECUTION
# ====================================================================

def main():
    print(f"Creating output directory '{Config.OUTPUT_DIR}/' if it doesn't exist...")
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    
    generator = DataGenerator()
    
    print("1/4 Generating Customer Profiles...")
    generator.generate_customers()
    df_customers = pd.DataFrame(generator.customers)
    
    print("2/4 Generating Transactions & Cybersecurity Telemetry...")
    generator.generate_events()
    df_transactions = pd.DataFrame(generator.transactions)
    df_security = pd.DataFrame(generator.security_logs)
    
    # Save base structural files for the project
    df_customers.to_csv(f"{Config.OUTPUT_DIR}/customer_profile.csv", index=False)
    
    # Exclude internal ground truth columns from the raw transaction output
    raw_txns = df_transactions.drop(columns=['_is_fraud', '_is_new_receiver', '_receiver_trust_score', '_receiver_risk_score'])
    raw_txns.to_csv(f"{Config.OUTPUT_DIR}/transactions.csv", index=False)
    
    df_security.to_csv(f"{Config.OUTPUT_DIR}/security_logs.csv", index=False)
    
    print("3/4 Correlating Data & Engineering ML Features...")
    df_ml = FeatureEngineer.correlate_datasets(df_customers, df_transactions, df_security)
    
    print("4/4 Saving ML Dataset...")
    df_ml.to_csv(f"{Config.OUTPUT_DIR}/ml_training_dataset.csv", index=False)
    
    print("\nDataset Generation Complete.")
    print(f"Generated Customers: {len(df_customers)}")
    print(f"Generated Events: {len(df_transactions)}")
    print(f"Total Correlated ML Rows: {len(df_ml)}")
    print(f"Fraud Ratio Achieved: {df_ml['is_fraud'].mean() * 100:.2f}%")
    print("Ready for FinSpark'26 Prototyping.")

if __name__ == "__main__":
    main()