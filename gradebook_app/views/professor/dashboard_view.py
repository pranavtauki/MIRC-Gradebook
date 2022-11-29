import pandas as pd
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.db.models import Avg, Max, Min, Count
from gradebook_app.models import Course
from gradebook_app.models import Evaluation
from gradebook_app.models import Marks
from gradebook_app.models.common_classes import ProfileType
from gradebook_app.models.evaluation_model import EvaluationForm, GradeFunctionForm
from gradebook_app.models.profile_model import ProfileCourse


def professor_dashboard(request, profile):
    courses = profile.courses.all()
    return render(request, f"professor/home.html", {'courses': courses})


def view_course_details(request, id):
    #mean = ProfileCourse.objects.filter(course__id=id).aggregate(num = Avg('score')).get("num")
    #max_score = ProfileCourse.objects.filter(course__id=id).aggregate(mx= Max('score')).get("mx")
    #min_score = ProfileCourse.objects.filter(course__id=id).aggregate(mn= Min('score')).get("mn")
    x = ProfileCourse.objects.filter(
        course_id=id,
        profile__type=ProfileType.STUDENT.value)
    y = x.aggregate(
        Avg('score'), Max('score'), Min('score')
    )
    print(y)
    top_students = x.order_by('-score')[:5].values('profile__first_name', 'profile__email', 'score')
    bottom_students = x.order_by('score')[:5].values('profile__first_name', 'profile__email', 'score')
    d = x.values('grade').annotate(count=Count('grade')).order_by('count')
    print(d)
    return render(request, 'professor/course_details.html', {
        
        'course_id': id,
        **y,
        'top_students': top_students,
        'bottom_students' : bottom_students,
        'grade_distribution' : d
    })




def view_students_list(request, id):
    students = []
    marks = []
    evals = []
    data = {}
    evalIDs = []
    df = pd.DataFrame({})
    try:
        students = Course.objects.get(id=id).profiles.filter(type=ProfileType.STUDENT.value).all()
        # for obj in Evaluation.objects.all():
        #     print(obj.name)
        marks = Marks.objects.filter(course_id=id).all()
        evals = Evaluation.objects.filter(course_id=id).all()
        evalIDs = [ev.id for ev in evals]
        for student in students:
            print(student.id)
            student_marks = []
            for evid in evalIDs:
                student_marks.append(
                    marks.filter(evaluation_id=evid, profile_id=student.id).values('marks'))  # change filter
            data[student.id] = student_marks
        df = pd.DataFrame(data, index=evalIDs)
        # print(student.id for student in students)
        print(df[3][1][0]['marks'])
    except Exception as e:
        print(e)
    return render(request, 'professor/students_list.html', {
        'students': students,
        'course_id': id,
        'evals': evals,
        'evalIDs': evalIDs,
        'df': df
    })


def evaluations_list(request, id):
    evaluations = []
    try:
        evaluations = Evaluation.objects.filter(course_id=id).all()
    except Exception as e:
        print(e)
    return render(request, 'professor/evaluations_list.html', {
        'evaluations': evaluations,
        'course_id': id
    })


def add_evaluation(request, id):
    form = EvaluationForm(request.POST)
    if form.is_valid():
        cleaned_data = form.cleaned_data
        e = {
            "id": request.session['eval_id'],
            'name': cleaned_data.get("name"),
            "eval_type": cleaned_data.get("eval_type"),
            "weight": cleaned_data.get("weight"),
            "max_marks": cleaned_data.get("max_marks")
        }
        request.session['evaluations'][request.session['eval_id']] = e
        request.session['eval_id'] = str(int(request.session['eval_id']) + 1)
        request.session.modified = True
        return redirect(configure_course, id=id)
    else:
        print("invalid form")


# def update_evaluation(request, eval_id):
#     evaluation = evaluations.get(eval_id)
#     if request.method == "POST":
#         form = EvaluationForm(request.POST, instance=evaluation)
#         if form.is_valid():
#             cleaned_data = form.cleaned_data
#             e = Evaluation(id=eval_id,
#                            name=cleaned_data.get("name"),
#                            eval_type=cleaned_data.get("eval_type"),
#                            weight=cleaned_data.get('weight'),
#                            max_marks=cleaned_data.get("max_marks"))
#             evaluations[e.id] = e
#         else:
#             print("Invalid Form")
#     else:
#         form = EvaluationForm(request.POST, instance=evaluation)
#         return render(request, "")

def delete_evaluation(request, course_id, eval_id):
    request.session['evaluations'].pop(str(eval_id))
    request.session.modified = True
    return redirect(configure_course, id=course_id)


def configure_course(request, id):
    if 'evaluations' not in request.session:
        request.session['evaluations'] = {}
    if 'eval_id' not in request.session:
        request.session['eval_id'] = 1
    if 'grade_function' not in request.session:
        request.session['grade_function'] = ""
    evals = request.session['evaluations']
    sum_ = sum(value['weight'] for key, value in evals.items())
    return render(request, f"professor/configure_course.html",
                  {'local_evaluations': evals.values(),
                   'add_evaluation_form': EvaluationForm(),
                   'sum': sum_,
                   'grade_function_form': GradeFunctionForm(),
                   'grade_function': request.session['grade_function'],
                   'course_id': id})


def add_course_configuration(request, id):
    evaluation_objs = []
    for eval in request.session['evaluations'].values():
        evaluation_objs.append(Evaluation(
            name=eval['name'],
            eval_type=eval['eval_type'],
            weight=eval['weight'],
            max_marks=eval['max_marks'],
            course_id=id
        )
        )
    Evaluation.objects.bulk_create(evaluation_objs)
    Course.objects.filter(id=id).update(thresholds=request.session['grade_function'])
    request.session['evaluations'].clear()
    request.session['eval_id'] = 1
    request.session['grade_function'] = ""
    request.session.modified = True
    return HttpResponse("Success")


def add_grade_function(request, id):
    form = GradeFunctionForm(request.POST)
    if form.is_valid():
        thresholds = []
        thresholds.append(form.cleaned_data.get("A"))
        thresholds.append(form.cleaned_data.get("B"))
        thresholds.append(form.cleaned_data.get("C"))
        thresholds.append(form.cleaned_data.get("D"))
        thresholds.append(form.cleaned_data.get("E"))
        thresholds.append(form.cleaned_data.get("F"))
        thresholds = list(map(int, thresholds))
        if thresholds == sorted(thresholds, reverse=True):
            thresholds = list(map(str, thresholds))
            request.session['grade_function'] = ",".join(thresholds)
            request.session.modified = True
        else:
            print("Wrong values")
    return redirect(configure_course, id=id)
