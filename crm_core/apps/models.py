from django.db import models
import uuid
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save

# --- Profile Model (यह लगभग सही था) ---
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    phone_number = models.CharField(max_length=15, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    branch_address = models.TextField(blank=True)
    reporting_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    monthly_target = models.DecimalField(max_digits=10, decimal_places=2, default=21000.00)
    
    ACCOUNT_STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Suspended', 'Suspended'),
    ]
    account_status = models.CharField(max_length=100, choices=ACCOUNT_STATUS_CHOICES, default='Active')

    def __str__(self):
        return f'{self.user.username} Profile'

# --- Client Model (इसमें सुधार किए गए हैं) ---
class Client(models.Model):
    # यह फील्ड ठीक था
    client_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # बदला गया: 'Users' की जगह 'User' और फील्ड का नाम 'agent' कर दिया गया
    agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='clients')

    # बाकी फील्ड्स ठीक थे
    customer_name = models.CharField(max_length=200)
    business_name = models.CharField(max_length=200, blank=True, null=True)
    business_address = models.TextField(blank=True, null=True)
    
    primary_phone = models.CharField(max_length=15)
    secondary_phone = models.CharField(max_length=15, blank=True, null=True)
    
    business_email = models.EmailField(blank=True, null=True)
    business_gst_number = models.CharField(max_length=50, blank=True, null=True)
    industry_type = models.CharField(max_length=100, blank=True, null=True)

    project_type = models.CharField(max_length=200)
    project_handover_date = models.DateField(blank=True, null=True)
    
    remark = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # सुधार: project_status के लिए Choices का इस्तेमाल किया गया
    STATUS_CHOICES = [
        ('New', 'New'),
        ('Contacted', 'Contacted'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    project_status = models.CharField(max_length=100, choices=STATUS_CHOICES, default='New')
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    advance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-created_at']  # Show newest first
        db_table = 'clients'


    @property
    def remaining_amount(self):
        """Calculate remaining amount after payments"""
        from django.db.models import Sum
        paid = self.payments.filter(is_verified=True).aggregate(
            total=Sum('amount')
        )['total'] or 0
        return self.total_amount - paid

    @property
    def phone_number(self):
        return self.primary_phone
    
    @property 
    def remarks(self):
        return self.remark or ""
    
    @property
    def location(self):
        return self.business_address or ""

    def __str__(self):
        return self.customer_name




# ... आपके मौजूदा मॉडल्स के बाद ...

# --- Payment Model (नया मॉडल) ---
# models.py में add करें अगर Payment model नहीं है

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('Cash', 'Cash'),
        ('Bank Transfer', 'Bank Transfer'),
        ('UPI', 'UPI'),
        ('Cheque', 'Cheque'),
        ('Card', 'Credit/Debit Card'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='Cash')
    payment_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Additional fields
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    is_verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payment_date']
        db_table = 'payments'
    
    def __str__(self):
        return f"{self.client.customer_name} - ₹{self.amount} ({self.payment_date.date()})"
    
    @property
    def formatted_amount(self):
        return f"₹{self.amount:,.0f}"

# ... Payment मॉडल के बाद ...

# --- Target Model (नया मॉडल) ---
class Target(models.Model):
    # यह टारगेट किस कर्मचारी के लिए है
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='targets')
    
    # टारगेट की राशि
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # यह टारगेट किस महीने और साल के लिए है
    month = models.PositiveIntegerField() # जैसे 6 (जून के लिए)
    year = models.PositiveIntegerField() # जैसे 2024

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # (Optional) टारगेट किसने सेट किया
    set_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='set_targets')

    class Meta:
        # यह सुनिश्चित करेगा कि एक यूज़र के लिए एक महीने में एक ही टारगेट हो
        unique_together = ('user', 'month', 'year')

    def __str__(self):
        # महीने के नाम के लिए एक helper
        import calendar
        month_name = calendar.month_name[self.month]
        return f'Target for {self.user.username} - {month_name} {self.year}'
    




class TeamMember(models.Model):
    ROLE_CHOICES = [
        ('Executive', 'Executive'),
        ('Team Leader', 'Team Leader'),
        ('Manager', 'Manager'),
        ('Admin', 'Admin'),
    ]
    
    DEPARTMENT_CHOICES = [
        ('Sales', 'Sales'),
        ('Marketing', 'Marketing'),
        ('Support', 'Support'),
        ('Management', 'Management'),
    ]
    
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.role})"
    




class ClientTransfer(models.Model):
    """Model to track client transfers between agents"""
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='transfers')
    from_agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transferred_clients')
    to_agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_clients')
    transferred_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_transfers')
    transfer_date = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-transfer_date']
        db_table = 'client_transfers'
    
    def __str__(self):
        return f"{self.client.customer_name} transferred from {self.from_agent.username} to {self.to_agent.username}"
    
    @property
    def transfer_summary(self):
        return f"Transfer #{self.id}: {self.client.customer_name} from {self.from_agent.get_full_name() or self.from_agent.username} to {self.to_agent.get_full_name() or self.to_agent.username}"