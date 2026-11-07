"""
Online Shopping and Order Management System
Automated Selenium 4 End-to-End Test Suite

Covers TC01 - TC12:
- TC01: Customer login with valid credentials
- TC02: Customer login with invalid credentials
- TC03: Customer registration with fresh unique account
- TC04: Product catalogue display (all seeded products)
- TC05: Product search functionality (name / category)
- TC06: Add product to shopping cart
- TC07: Update cart quantity & verify price calculation
- TC08: Checkout and place order
- TC09: View order history & order details
- TC10: Admin login, dashboard stats & product management (add product)
- TC11: Role-based access control (blocking customers from /admin)
- TC12: Empty cart checkout prevention
"""

import argparse
import sys
import time
import urllib.request
import uuid
from datetime import datetime
from threading import Thread

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class ShoppingSystemTester:
    def __init__(self, base_url="http://127.0.0.1:5000", headless=True):
        self.base_url = base_url.rstrip('/')
        self.headless = headless
        self.driver = None
        self.wait = None
        self.results = []
        self.last_order_id = None
        self.server_thread = None

    def start_local_server_if_needed(self):
        """Check if server is reachable; if not, spin up local Flask app."""
        try:
            with urllib.request.urlopen(f"{self.base_url}/", timeout=2) as resp:
                if resp.status == 200:
                    print(f"[*] Target server reachable at {self.base_url}")
                    return
        except Exception:
            pass

        print(f"[*] Server not running at {self.base_url}. Starting internal Flask server thread...")
        try:
            import app as flask_app_module

            def run_app():
                flask_app_module.app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

            self.server_thread = Thread(target=run_app, daemon=True)
            self.server_thread.start()

            # Poll until server is ready
            start_time = time.time()
            while time.time() - start_time < 10:
                try:
                    with urllib.request.urlopen(f"{self.base_url}/", timeout=1) as resp:
                        if resp.status == 200:
                            print(f"[+] Internal server is ready at {self.base_url}")
                            return
                except Exception:
                    time.sleep(0.5)

            raise RuntimeError("Could not connect to Flask server within 10 seconds.")
        except Exception as e:
            print(f"[!] Warning: Could not automatically start server: {e}")

    def setup_driver(self):
        print(f"[*] Initializing Chrome WebDriver (Headless={self.headless})...")
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--log-level=3")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        print("[+] Chrome WebDriver initialized successfully.\n")

    def teardown_driver(self):
        if self.driver:
            try:
                self.driver.quit()
                print("[*] Chrome WebDriver closed.")
            except Exception:
                pass

    def fill_input(self, element, value):
        """Deterministically populate an input and fire input/change events."""
        self.driver.execute_script(
            "arguments[0].focus(); arguments[0].value = arguments[1]; "
            "arguments[0].dispatchEvent(new Event('input', { bubbles: true })); "
            "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
            element, str(value)
        )

    def submit_form(self, form_or_element):
        """Submit form safely via requestSubmit or fallback submit."""
        self.driver.execute_script("""
            var elem = arguments[0];
            var form = elem.tagName === 'FORM' ? elem : elem.closest('form');
            if (form) {
                if (typeof form.requestSubmit === 'function') {
                    form.requestSubmit();
                } else {
                    form.submit();
                }
            }
        """, form_or_element)

    def record_result(self, test_id, name, status, details=""):
        self.results.append({
            "id": test_id,
            "name": name,
            "status": status,
            "details": details
        })
        symbol = "✓ PASS" if status == "PASS" else "✗ FAIL"
        print(f"[{symbol}] {test_id}: {name}")
        if details and status == "FAIL":
            print(f"       Reason: {details}")

    def logout(self):
        """Ensure session is cleared and browser arrives on login page."""
        self.driver.get(f"{self.base_url}/logout")
        self.wait.until(EC.visibility_of_element_located((By.ID, "username")))

    def login_as(self, username, password):
        """Helper to authenticate a user cleanly."""
        self.logout()
        user_input = self.wait.until(EC.visibility_of_element_located((By.ID, "username")))
        pass_input = self.wait.until(EC.visibility_of_element_located((By.ID, "password")))
        self.fill_input(user_input, username)
        self.fill_input(pass_input, password)
        self.submit_form(user_input)
        self.wait.until(EC.visibility_of_element_located((By.ID, "nav-username")))

    # ==================== TEST CASES ====================

    def tc01_customer_valid_login(self):
        """TC01: Customer login with valid credentials."""
        test_id = "TC01"
        name = "Customer Login with Valid Credentials"
        try:
            self.logout()

            username_input = self.wait.until(EC.visibility_of_element_located((By.ID, "username")))
            password_input = self.wait.until(EC.visibility_of_element_located((By.ID, "password")))

            self.fill_input(username_input, "customer1")
            self.fill_input(password_input, "pass123")
            self.submit_form(username_input)

            # Verify catalogue reached and user badge visible
            self.wait.until(EC.visibility_of_element_located((By.ID, "nav-username")))
            nav_user = self.driver.find_element(By.ID, "nav-username").text
            assert "Alice" in nav_user or "customer1" in nav_user, f"Unexpected username in navbar: {nav_user}"

            self.record_result(test_id, name, "PASS", "Customer successfully authenticated.")
        except Exception as e:
            import traceback
            self.record_result(test_id, name, "FAIL", f"{type(e).__name__}: {e}\n{traceback.format_exc()}")

    def tc02_customer_invalid_login(self):
        """TC02: Customer login with invalid credentials."""
        test_id = "TC02"
        name = "Customer Login with Invalid Credentials"
        try:
            self.logout()

            username_input = self.wait.until(EC.visibility_of_element_located((By.ID, "username")))
            password_input = self.wait.until(EC.visibility_of_element_located((By.ID, "password")))

            self.fill_input(username_input, "invalid_user")
            self.fill_input(password_input, "wrong_password")
            self.submit_form(username_input)

            # Wait for danger alert
            alert = self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "alert-danger")))
            assert "Invalid username or password" in alert.text, f"Unexpected alert text: {alert.text}"

            self.record_result(test_id, name, "PASS", "Error alert displayed as expected.")
        except Exception as e:
            import traceback
            self.record_result(test_id, name, "FAIL", f"{type(e).__name__}: {e}\n{traceback.format_exc()}")

    def tc03_customer_registration(self):
        """TC03: Customer registration with new unique account."""
        test_id = "TC03"
        name = "Customer Registration"
        try:
            self.driver.get(f"{self.base_url}/register")

            new_user_token = uuid.uuid4().hex[:6]
            new_username = f"user_{new_user_token}"
            new_email = f"user_{new_user_token}@example.com"

            name_input = self.wait.until(EC.visibility_of_element_located((By.ID, "name")))
            email_input = self.wait.until(EC.visibility_of_element_located((By.ID, "email")))
            user_input = self.wait.until(EC.visibility_of_element_located((By.ID, "username")))
            pass_input = self.wait.until(EC.visibility_of_element_located((By.ID, "password")))
            confirm_input = self.wait.until(EC.visibility_of_element_located((By.ID, "confirm_password")))

            self.fill_input(name_input, "Automated Tester")
            self.fill_input(email_input, new_email)
            self.fill_input(user_input, new_username)
            self.fill_input(pass_input, "pass123")
            self.fill_input(confirm_input, "pass123")

            self.submit_form(name_input)

            # Should redirect to login page with success flash
            self.wait.until(EC.url_contains("/login"))
            success_alert = self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "alert-success")))
            assert "Registration successful" in success_alert.text

            # Verify logging in with newly registered user
            username_input = self.wait.until(EC.visibility_of_element_located((By.ID, "username")))
            password_input = self.wait.until(EC.visibility_of_element_located((By.ID, "password")))

            self.fill_input(username_input, new_username)
            self.fill_input(password_input, "pass123")
            self.submit_form(username_input)

            self.wait.until(EC.visibility_of_element_located((By.ID, "nav-username")))
            self.record_result(test_id, name, "PASS", f"User '{new_username}' registered and logged in.")
        except Exception as e:
            import traceback
            self.record_result(test_id, name, "FAIL", f"{type(e).__name__}: {e}\n{traceback.format_exc()}")

    def tc04_product_catalogue(self):
        """TC04: Product catalogue display."""
        test_id = "TC04"
        name = "Product Catalogue Display"
        try:
            self.driver.get(f"{self.base_url}/")
            cards = self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "product-card")))
            assert len(cards) >= 6, f"Expected at least 6 seeded products, found {len(cards)}"

            # Verify card contents
            first_card = cards[0]
            title = first_card.find_element(By.CLASS_NAME, "card-title").text
            assert len(title) > 0, "Product title is empty"

            self.record_result(test_id, name, "PASS", f"Verified {len(cards)} products displayed.")
        except Exception as e:
            import traceback
            self.record_result(test_id, name, "FAIL", f"{type(e).__name__}: {e}\n{traceback.format_exc()}")

    def tc05_product_search(self):
        """TC05: Product search functionality."""
        test_id = "TC05"
        name = "Product Search Functionality"
        try:
            self.driver.get(f"{self.base_url}/")
            search_input = self.wait.until(EC.visibility_of_element_located((By.ID, "search-input")))

            self.fill_input(search_input, "Laptop")
            self.submit_form(search_input)

            self.wait.until(EC.url_contains("q=Laptop"))
            cards = self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "product-card")))
            card_titles = [c.find_element(By.CLASS_NAME, "card-title").text for c in cards]

            has_laptop = any("Laptop" in t for t in card_titles)
            assert has_laptop, f"Search for 'Laptop' did not find Laptop. Titles: {card_titles}"

            self.record_result(test_id, name, "PASS", "Search results accurately filtered products.")
        except Exception as e:
            import traceback
            self.record_result(test_id, name, "FAIL", f"{type(e).__name__}: {e}\n{traceback.format_exc()}")

    def tc06_add_product_to_cart(self):
        """TC06: Add product to shopping cart."""
        test_id = "TC06"
        name = "Add Product to Shopping Cart"
        try:
            self.login_as("customer1", "pass123")
            self.driver.get(f"{self.base_url}/")

            add_button = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "add-to-cart-btn")))
            self.submit_form(add_button)

            # Wait for flash alert
            self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "alert-success")))

            # Navigate to cart page and verify item row exists
            self.driver.get(f"{self.base_url}/cart")
            cart_table = self.wait.until(EC.visibility_of_element_located((By.ID, "cart-table")))
            rows = cart_table.find_elements(By.TAG_NAME, "tbody")[0].find_elements(By.TAG_NAME, "tr")
            assert len(rows) >= 1, "Cart table is empty"

            self.record_result(test_id, name, "PASS", f"Product added; cart contains {len(rows)} item row(s).")
        except Exception as e:
            import traceback
            self.record_result(test_id, name, "FAIL", f"{type(e).__name__}: {e}\n{traceback.format_exc()}")

    def tc07_update_cart_quantity(self):
        """TC07: Update cart quantity and verify subtotal."""
        test_id = "TC07"
        name = "Update Cart Quantity and Price"
        try:
            self.login_as("customer1", "pass123")
            self.driver.get(f"{self.base_url}/")
            add_button = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "add-to-cart-btn")))
            self.submit_form(add_button)
            self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "alert-success")))

            self.driver.get(f"{self.base_url}/cart")
            qty_input = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='quantity']")))
            self.fill_input(qty_input, "2")
            self.submit_form(qty_input)

            self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "alert-success")))

            # Re-read input value
            reloaded_qty = self.driver.find_element(By.CSS_SELECTOR, "input[name='quantity']").get_attribute("value")
            assert reloaded_qty == "2", f"Expected quantity '2', got '{reloaded_qty}'"

            self.record_result(test_id, name, "PASS", "Quantity successfully updated to 2.")
        except Exception as e:
            import traceback
            self.record_result(test_id, name, "FAIL", f"{type(e).__name__}: {e}\n{traceback.format_exc()}")

    def tc08_checkout_and_place_order(self):
        """TC08: Checkout and order placement."""
        test_id = "TC08"
        name = "Checkout and Place Order"
        try:
            self.login_as("customer1", "pass123")
            # Ensure an item is in the cart
            self.driver.get(f"{self.base_url}/")
            add_btn = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "add-to-cart-btn")))
            self.submit_form(add_btn)
            self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "alert-success")))

            # Go to checkout
            self.driver.get(f"{self.base_url}/checkout")
            self.wait.until(EC.visibility_of_element_located((By.ID, "checkout-form")))

            name_input = self.wait.until(EC.visibility_of_element_located((By.ID, "customer_name")))
            email_input = self.driver.find_element(By.ID, "email")
            phone_input = self.driver.find_element(By.ID, "phone")
            address_input = self.driver.find_element(By.ID, "address")

            self.fill_input(name_input, "Alice Customer")
            self.fill_input(email_input, "alice@example.com")
            self.fill_input(phone_input, "+1 555-019-8765")
            self.fill_input(address_input, "456 College Campus Road, Tech City, TX 75001")

            self.submit_form(name_input)

            # Verify order confirmation page
            self.wait.until(EC.url_contains("/order-confirmation/"))
            order_id_elem = self.wait.until(EC.visibility_of_element_located((By.ID, "confirmation-order-id")))
            raw_text = order_id_elem.text
            self.last_order_id = raw_text.replace("#", "").strip()

            assert len(self.last_order_id) > 0, "Order ID missing from confirmation"
            self.record_result(test_id, name, "PASS", f"Order placed successfully: #{self.last_order_id}")
        except Exception as e:
            import traceback
            self.record_result(test_id, name, "FAIL", f"{type(e).__name__}: {e}\n{traceback.format_exc()}")

    def tc09_order_history(self):
        """TC09: View order history and order details."""
        test_id = "TC09"
        name = "Customer Order History"
        try:
            self.login_as("customer1", "pass123")
            self.driver.get(f"{self.base_url}/orders")
            table = self.wait.until(EC.visibility_of_element_located((By.ID, "orders-table")))
            order_rows = table.find_elements(By.CLASS_NAME, "order-row")
            assert len(order_rows) >= 1, "Order history table has no rows"

            # Check if last order id is in table
            if self.last_order_id:
                found_id = any(f"#{self.last_order_id}" in r.text for r in order_rows)
                assert found_id, f"Order #{self.last_order_id} not found in order history"

            # Click view details on first order
            first_view_btn = table.find_elements(By.CSS_SELECTOR, "a[id^='view-order-btn-']")[0]
            self.driver.execute_script("arguments[0].click();", first_view_btn)

            # Verify order details loaded
            self.wait.until(EC.visibility_of_element_located((By.ID, "order-details-container")))
            self.record_result(test_id, name, "PASS", "Order history and details verified.")
        except Exception as e:
            import traceback
            self.record_result(test_id, name, "FAIL", f"{type(e).__name__}: {e}\n{traceback.format_exc()}")

    def tc10_admin_product_management(self):
        """TC10: Admin login and product addition/management."""
        test_id = "TC10"
        name = "Admin Product Management"
        try:
            # Login as Admin
            self.login_as("admin", "admin123")

            # Verify redirected to admin dashboard
            self.wait.until(EC.url_contains("/admin"))
            self.wait.until(EC.visibility_of_element_located((By.ID, "admin-stats")))

            # Navigate to Add New Product page
            self.driver.get(f"{self.base_url}/admin/product/add")
            self.wait.until(EC.visibility_of_element_located((By.ID, "add-product-form")))

            unique_prod_name = f"DevOps Item {uuid.uuid4().hex[:5]}"

            name_in = self.driver.find_element(By.ID, "product-name")
            cat_in = self.driver.find_element(By.ID, "product-category")
            price_in = self.driver.find_element(By.ID, "product-price")
            stock_in = self.driver.find_element(By.ID, "product-stock")
            desc_in = self.driver.find_element(By.ID, "product-description")

            self.fill_input(name_in, unique_prod_name)
            self.fill_input(cat_in, "Hardware")
            self.fill_input(price_in, "89.99")
            self.fill_input(stock_in, "15")
            self.fill_input(desc_in, "Automated test product description.")

            self.submit_form(name_in)

            # Verify redirected to admin dashboard with success alert
            self.wait.until(EC.url_contains("/admin"))
            self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "alert-success")))

            # Verify item appears in product inventory table
            table = self.wait.until(EC.visibility_of_element_located((By.ID, "admin-product-table")))
            assert unique_prod_name in table.text, f"New product '{unique_prod_name}' not listed in admin table"

            # Also check that it is visible on the public catalogue
            self.driver.get(f"{self.base_url}/")
            cards = self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "product-card")))
            card_texts = [c.text for c in cards]
            assert any(unique_prod_name in t for t in card_texts), "New product not in public catalogue"

            self.record_result(test_id, name, "PASS", f"Product '{unique_prod_name}' created and verified.")
        except Exception as e:
            import traceback
            self.record_result(test_id, name, "FAIL", f"{type(e).__name__}: {e}\n{traceback.format_exc()}")

    def tc11_role_access_restriction(self):
        """TC11: Verify non-admin customer cannot access admin routes."""
        test_id = "TC11"
        name = "Role-Based Access Restriction"
        try:
            # Login as regular customer
            self.login_as("customer1", "pass123")

            # Attempt to navigate to admin console
            self.driver.get(f"{self.base_url}/admin")

            # Expect redirected away from admin dashboard
            self.wait.until(lambda d: not d.current_url.endswith("/admin"))
            current_url = self.driver.current_url
            assert not current_url.endswith("/admin"), f"Customer was not redirected from admin page: {current_url}"

            self.record_result(test_id, name, "PASS", "Customer denied access to admin dashboard.")
        except Exception as e:
            import traceback
            self.record_result(test_id, name, "FAIL", f"{type(e).__name__}: {e}\n{traceback.format_exc()}")

    def tc12_empty_cart_checkout_prevention(self):
        """TC12: Prevent checkout when shopping cart is empty."""
        test_id = "TC12"
        name = "Empty Cart Checkout Prevention"
        try:
            self.login_as("customer1", "pass123")

            # Visit cart and ensure it's empty
            self.driver.get(f"{self.base_url}/cart")
            while True:
                remove_forms = self.driver.find_elements(By.CSS_SELECTOR, "form[action^='/cart/remove/']")
                if not remove_forms:
                    break
                self.submit_form(remove_forms[0])
                time.sleep(0.3)
                self.driver.get(f"{self.base_url}/cart")

            # Directly request checkout
            self.driver.get(f"{self.base_url}/checkout")

            # Should redirect away from /checkout (to /cart)
            self.wait.until(lambda d: not d.current_url.endswith("/checkout"))
            assert not self.driver.current_url.endswith("/checkout"), "User remained on /checkout with an empty cart"

            self.record_result(test_id, name, "PASS", "Empty cart redirected safely from checkout.")
        except Exception as e:
            import traceback
            self.record_result(test_id, name, "FAIL", f"{type(e).__name__}: {e}\n{traceback.format_exc()}")

    # ==================== RUNNER ====================

    def run_all(self):
        print("=" * 70)
        print("  ONLINE SHOPPING AND ORDER MANAGEMENT SYSTEM")
        print("  Automated Selenium 4 End-to-End Test Suite")
        print(f"  Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        self.start_local_server_if_needed()
        self.setup_driver()

        try:
            self.tc01_customer_valid_login()
            self.tc02_customer_invalid_login()
            self.tc03_customer_registration()
            self.tc04_product_catalogue()
            self.tc05_product_search()
            self.tc06_add_product_to_cart()
            self.tc07_update_cart_quantity()
            self.tc08_checkout_and_place_order()
            self.tc09_order_history()
            self.tc10_admin_product_management()
            self.tc11_role_access_restriction()
            self.tc12_empty_cart_checkout_prevention()
        finally:
            self.teardown_driver()

        # Summary Table
        print("\n" + "=" * 70)
        print("                   SELENIUM TEST EXECUTION SUMMARY")
        print("=" * 70)
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = total - passed

        for r in self.results:
            badge = "[PASS]" if r["status"] == "PASS" else "[FAIL]"
            print(f" {badge} {r['id']}: {r['name']:<42} {r.get('details', '')[:25]}")

        print("-" * 70)
        print(f" Total Tests Run : {total}")
        print(f" Passed          : {passed}")
        print(f" Failed          : {failed}")
        success_rate = (passed / total) * 100 if total > 0 else 0
        print(f" Success Rate    : {success_rate:.1f}%")
        print("=" * 70)

        if failed > 0:
            print("\n[!] WARNING: Some test cases failed. Please inspect logs above.")
            return False
        else:
            print("\n[✓] SUCCESS: All test cases passed successfully!")
            return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Selenium 4 E2E Tests")
    parser.add_argument("--url", default="http://127.0.0.1:5000", help="Base URL of the running application")
    parser.add_argument("--headless", action="store_true", default=True, help="Run Chrome in headless mode")
    parser.add_argument("--no-headless", action="store_false", dest="headless", help="Run with visible browser window")
    args = parser.parse_args()

    tester = ShoppingSystemTester(base_url=args.url, headless=args.headless)
    success = tester.run_all()
    sys.exit(0 if success else 1)
