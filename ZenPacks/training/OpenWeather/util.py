import re


def camelCaseToSnake(camelCaseString):
    """
    Convert string from CamelCase to snake_case

    Args:
        camelCaseString (str): The CamelCase string to be converted to the snake_case

    Returns:
        str: The snake_case string

    Examples:
        >>> camelCaseToSnake('CamelCase')
        'camel_case'
        >>> camelCaseToSnake('Camel2Case')
        'camel2_case'
        >>> camelCaseToSnake('getHTTPResponseCode')
        'get_http_response_code'
    """
    firstStep = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camelCaseString)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', firstStep).lower()
