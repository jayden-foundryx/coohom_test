def kujiale_task_listing(self, cron, api, design_id, order_design_id,
                            order_type):
    sign = self._get_sign(False, api)
    params = {
        "appkey": api['api_key'],
        "timestamp": api['timestamp'],
        "sign": sign,
        "designId": design_id,
    }
    data = {
        "designId": design_id,
        "type": 1 if order_type == '全屋家具' else 0,
        "obsAuditDesignId": order_design_id,
        "orderDesignType": "audit"
    }
    data_for_log = json.dumps(data, indent=2)
    data = json.dumps(data)
    api_url = api['api_url'] + '/task/listing'
    try:
        response = requests.post(api_url, params=params,
                                    headers=api['headers'], data=data)
        response = response.json()
    except Exception as e:
        if not cron:
            raise ValidationError(str(e))
        else:
            message = "Something is wrong!" + str(e)
            status = 500
            self.create_log(message, status, data_for_log, 'task_listing')
    if response.get('c') and response.get('c') != '0':
        if not cron:
            raise ValidationError(response.get('m'))
        else:
            message = "Something is wrong!" + response.get('m')
            status = 500
            self.create_log(message, status, data_for_log, 'task_listing')
    else:
        result = response.get('d')
        if result:
            message = f"Successful!\ntaskID: {result}"
            status = 200
            self.create_log(message, status, data_for_log, 'task_listing')
            return result
        else:
            if not cron:
                raise ValidationError('No result found in response')
            else:
                message = "Something is wrong! No result found in response"
                status = 500
                self.create_log(message, status, data_for_log, 'task_listing')
                return False
