# graph/business_policy_store.py

BUSINESS_POLICIES = {
    "refund_window": {
        "title": "Refund Time Window",
        "rule": (
            "Refunds are only available within 14 days of delivery. "
            "Items must be unused and returned in their original packaging."
        ),
        "exceptions": [
            "damaged_item",
            "wrong_item_sent"
        ]
    },

    "post_delivery_cancellation": {
        "title": "Post-Delivery Cancellation",
        "rule": (
            "Orders cannot be cancelled once delivery is completed. "
            "Customers may request a return instead if eligible."
        )
    },

    "digital_goods": {
        "title": "Digital Goods Policy",
        "rule": (
            "Digital products such as downloads or coupon codes are non-refundable "
            "once they have been delivered or accessed."
        ),
        "exceptions": [
            "system_error"
        ]
    },

    "billing_dispute_window": {
        "title": "Billing Dispute Window",
        "rule": (
            "Billing disputes must be reported within 30 days of the payment date."
        )
    },

    "account_verification": {
        "title": "Account Verification Requirement",
        "rule": (
            "For account-related or sensitive billing requests, identity verification "
            "is required before any changes can be made."
        )
    }
}
