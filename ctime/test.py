from django.shortcuts import render_to_response

def test(request):
  query = request.GET.get('q','') #request.GET是一个类字典对象，它包含所有GET请求的参数，这里表示取得name为'q'的参数值
  if query:
    results = 'You just sent %s' % query
  else:
    results = []
  return render_to_response('test01..html', {'results': results})
