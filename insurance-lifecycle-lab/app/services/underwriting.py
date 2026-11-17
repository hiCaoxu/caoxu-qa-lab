from decimal import Decimal


def auto_underwrite(application, product):
    if application.insured_id_no.endswith("0000"):
        return "REJECTED", "BLACKLIST_ID_ENDING", "AUTO"

    limit = Decimal(str(product.auto_approve_limit))
    if Decimal(str(application.sum_insured)) > limit:
        return "UNDERWRITING", "MANUAL_REVIEW_REQUIRED", "AUTO"

    return "APPROVED", "AUTO_APPROVED", "AUTO"
