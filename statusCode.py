class Code:
    succeed = dict({'code':'000','message':'succeed'})
    default_failed = dict({'code':'001','message':'failed'})
    missing_argument = dict({'code':'002','message':'missing argument'})
    something_empty = dict({'code':'003','message':'something is empty'})
    user_exisit = dict({'code':'004','message':'user already exisit'})
    user_do_not_exisit = dict({'code':'005','message':'user does not exisit'})
    login_failed = dict({'code':'006','message':'login failed'})


## 用來當作 Response 的物件
def response(status_code ,data = None):
    result = status_code
    if data is not None:
        result['data'] = data
    return result

if __name__ == "__main__":
    pass