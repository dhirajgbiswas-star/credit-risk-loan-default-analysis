from src.analysis.expected_loss import calculate_expected_loss


def test_expected_loss():
    assert calculate_expected_loss(pd=0.10, lgd=0.50, ead=100000) == 5000


def test_expected_loss_zero_pd():
    assert calculate_expected_loss(pd=0.0, lgd=0.60, ead=25000) == 0
