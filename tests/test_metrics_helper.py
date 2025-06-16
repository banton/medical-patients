"""Helper functions for testing Prometheus metrics."""


def get_metric_value(metric, labels_dict=None):
    """
    Get the current value of a Prometheus metric.
    
    Args:
        metric: The prometheus metric object
        labels_dict: Dictionary of label values to match
        
    Returns:
        The metric value or 0 if not found
    """
    for metric_family in metric.collect():
        for sample in metric_family.samples:
            # Skip _created and other suffixes
            if sample.name.endswith('_total') or sample.name.endswith('_bucket') or sample.name.endswith('_sum'):
                if labels_dict is None or sample.labels == labels_dict:
                    return sample.value
            elif not any(sample.name.endswith(suffix) for suffix in ['_created', '_count', '_bucket', '_sum']):
                # For gauges and other metrics without suffix
                if labels_dict is None or sample.labels == labels_dict:
                    return sample.value
    return 0