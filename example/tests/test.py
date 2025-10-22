import unittest

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from tests.pages.base import BasePage
from tests.pages.home import HomePage
from tests.pages.cart import CartPage
from tests.pages.product import ProductPage


# HEADLESS = True
HEADLESS = False
BASE_URL = "https://altwalker.github.io/jekyll-ecommerce/"

driver = None


def setUpRun():
    """Setup the webdriver."""

    global driver

    options = Options()
    if HEADLESS:
        options.add_argument("-headless")

    print("Create a new Firefox session")
    driver = webdriver.Firefox(options=options)

    print("Set implicitly wait")
    driver.implicitly_wait(15)
    print("Window size: {width}x{height}".format(**driver.get_window_size()))


def tearDownRun():
    """Close the webdriver."""

    global driver

    print("Close the Firefox session")
    driver.quit()


class BaseModel(unittest.TestCase):
    """Contains common methods for all models."""

    def setUpModel(self):
        global driver

        print("Set up for: {}".format(type(self).__name__))
        self.driver = driver

    def v_homepage(self):
        page = HomePage(self.driver)

        self.assertTrue(page.is_cart_button_present, "Cart button should be presents.")
        self.assertTrue(
            page.is_products_list_present, "Products list should be present."
        )

    def v_cart_open_and_not_empty(self):
        page = CartPage(self.driver)
        page.wait_for_snipcart()

        print("Items in cart: {}".format(page.total_items_in_cart))

        self.assertTrue(page.is_cart_open, "Cart should be open.")
        self.assertTrue(
            page.is_content_next_button_present,
            "Content next step button should be presents.",
        )
        self.assertGreater(
            page.total_items_in_cart, 0, "Should have at least one item in cart."
        )

    def e_do_nothing(self):
        pass


class NavigationModel(BaseModel):
    def v_product_page(self):
        page = ProductPage(self.driver)

        print("Product: {}".format(page.product_name))

        self.assertTrue(page.is_product_present)

    def v_homepage_cart_open(self):
        page = BasePage(self.driver)
        self.assertTrue(page.is_cart_open, "Cart should be open.")

    def v_product_page_cart_open(self):
        page = BasePage(self.driver)
        self.assertTrue(page.is_cart_open, "Cart should be open.")

    def e_load_home_page(self):
        print("Load the e-commerce homepage from: {}".format(BASE_URL))

        page = HomePage(self.driver, BASE_URL)
        page.open()

    def e_add_to_cart_from_homepage(self):
        page = HomePage(self.driver)

        page.add_to_cart_random_product()
        page.wait_for_cart_reload()

        print("Items in cart: {}".format(page.total_items_in_cart))

    def e_go_to_product_page(self):
        page = HomePage(self.driver)
        page.click_random_product()

    def e_close_cart(self):
        page = BasePage(self.driver)
        page.click_close_cart_button()

    def e_go_to_homepage(self):
        page = BasePage(self.driver)
        page.click_home_button()

    def e_add_to_cart_from_product_page(self):
        page = ProductPage(self.driver)
        page.click_add_to_cart()
        page.wait_for_cart_reload()

    def e_open_cart(self):
        page = BasePage(self.driver)
        page.click_cart_button()

    def e_close_cart_and_go_to_homepage(self):
        page = BasePage(self.driver)
        page.click_close_cart_button()
        page.click_home_button()


class CheckoutModel(BaseModel):
    def v_billing_address(self):
        page = CartPage(self.driver)
        page.wait_for_snipcart()

        self.assertTrue(
            page.is_billing_next_button_present,
            "Billing next step button should be presents.",
        )

    def v_payment_method(self):
        page = CartPage(self.driver)
        page.wait_for_snipcart()

        self.assertTrue(
            page.is_payment_next_button_present,
            "Payment next step button should be presents.",
        )

    def v_order_confirmation(self):
        page = CartPage(self.driver)
        page.wait_for_snipcart()

        self.assertTrue(
            page.is_order_confirmation_present,
            "Order next step button should be presents.",
        )

    def v_order_confirmed(self):
        page = BasePage(self.driver)
        page.wait_for_snipcart()

    def e_go_to_billing_address(self):
        page = CartPage(self.driver)

        page.click_content_cart_next_step_button()

    def e_fill_billing_and_go_to_payment(self):
        page = CartPage(self.driver)
        page.fill_in_billing_adress_form(
            name="Altwalker",
            city="Cluj-Napoca",
            email="hello@test.test",
            postal_code=42012,
            street_address1="42 Cloud Street",
        )

        page.click_billing_addres_next_step_button()

    def e_fill_payment_and_go_to_confirmation(self):
        page = CartPage(self.driver)

        page.click_payment_next_step_button()

    def e_place_order(self):
        page = CartPage(self.driver)

        page.click_order_confirmation_place_order_button()

    def e_go_to_homepage(self):
        page = BasePage(self.driver)

        page.click_close_cart_button()
        page.click_home_button()
