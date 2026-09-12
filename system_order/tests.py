from decimal import Decimal
from django.test import TestCase
from menu_product.models import Category, Product
from .models import Order, OrderItem

class OrderModelTest(TestCase):
    def setUp(self):
        """Menyiapkan data dummy sebelum setiap fungsi test dijalankan."""
        self.category = Category.objects.create(name="Minuman")
        self.product_espresso = Product.objects.create(
            category=self.category,
            name="Espresso",
            price=Decimal("18000.00"),
            is_available=True
        )
        self.product_croissant = Product.objects.create(
            category=self.category,
            name="Croissant",
            price=Decimal("25000.00"),
            is_available=True
        )
        self.order = Order.objects.create(customer_name="Naufal")

    def test_price_snapshot_and_total_amount_calculation(self):
        """
        1. Memastikan harga produk ter-snapshot otomatis ke OrderItem.
        2. Memastikan total_amount di Order bertambah sesuai (quantity * price).
        """
        item1 = OrderItem.objects.create(
            order=self.order,
            product=self.product_espresso,
            quantity=2  # 2 x 18.000 = 36.000
        )
        
        # Reload order dari DB untuk ambil nilai total_amount terbaru
        self.order.refresh_from_db()
        
        # Assertion 1: Snapshot harga berhasil
        self.assertEqual(item1.price, Decimal("18000.00"))
        # Assertion 2: Total belanjaan pas (36.000)
        self.assertEqual(self.order.total_amount, Decimal("36000.00"))

    def test_price_snapshot_impenetrable_to_master_price_change(self):
        """
        Memastikan jika harga master Product diubah di kemudian hari,
        harga di OrderItem yang sudah dibeli TIDAK ikut berubah.
        """
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product_espresso,
            quantity=1
        )
        
        # Ubah harga master Espresso di menu dari 18.000 jadi 25.000
        self.product_espresso.price = Decimal("25000.00")
        self.product_espresso.save()

        # Reload item dari DB
        item.refresh_from_db()

        # Price di OrderItem harus tetap 18.000!
        self.assertEqual(item.price, Decimal("18000.00"))

    def test_total_amount_recalculation_on_item_delete(self):
        """
        Memastikan jika item dihapus dari pesanan, total_amount
        di Order berkurang/dihitung ulang secara otomatis.
        """
        item1 = OrderItem.objects.create(
            order=self.order,
            product=self.product_espresso,
            quantity=1  # 18.000
        )
        item2 = OrderItem.objects.create(
            order=self.order,
            product=self.product_croissant,
            quantity=1  # 25.000
        )

        self.order.refresh_from_db()
        self.assertEqual(self.order.total_amount, Decimal("43000.00"))

        # Hapus Croissant dari order
        item2.delete()

        self.order.refresh_from_db()
        # Total harus kembali menjadi 18.000
        self.assertEqual(self.order.total_amount, Decimal("18000.00"))