from django.urls import reverse, NoReverseMatch

simple = [
    'accounts:dashboard', 'accounts:password_change', 'accounts:logout',
    'students:list', 'students:add',
    'courses:departments', 'courses:list', 'courses:subjects', 'courses:enrollments',
    'attendance:list', 'attendance:mark',
    'results:exams', 'results:exam_add', 'results:my',
]
with_id = ['students:detail', 'students:edit', 'students:delete', 'results:marks']

for name in simple:
    try:
        print('OK  ', name, reverse(name))
    except NoReverseMatch:
        print('FAIL', name)

for name in with_id:
    try:
        print('OK  ', name, reverse(name, args=[1]))
    except NoReverseMatch:
        print('FAIL', name)