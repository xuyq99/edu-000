from rest_framework.serializers import ModelSerializer

from course.models import CourseCategory, Course, Teacher, CourseChapter, CourseLesson


# 课程分类序列化器
class CourseCategoryModelSerializer(ModelSerializer):
    class Meta:
        model = CourseCategory
        fields = ('name', 'id')


# 讲师序列化
class TeacherModelSerializer(ModelSerializer):
    class Meta:
        model = Teacher
        fields = ('id', 'name', 'title', 'signature', 'image')


# 课程序列化器
class CourseModelSerializer(ModelSerializer):
    # 将讲师显示序列化的信息，调用一下
    teacher = TeacherModelSerializer()

    class Meta:
        model = Course
        fields = ('id', 'name', 'course_img', 'students', 'lessons',
                  'pub_lessons', 'price', 'teacher', 'lesson_list',
                  'discount_name', 'active_time', 'real_price', )


# 课程详细信息序列化器
class CourseDetailModelSerializer(ModelSerializer):

    teacher = TeacherModelSerializer()

    class Meta:
        model = Course
        fields = ('id', 'name', 'students', 'course_img', 'lessons',
                  'pub_lessons', 'price', 'teacher', 'course_chapter_list','level_name',
                  'course_category',  'brief_html','file_path', 'real_price', 'active_time',
                  'brief_html', 'lesson_list', 'discount_name', )


# # 课程课时序列化器
class CourseLessonModelSerializer(ModelSerializer):
    class Meta:
        model = CourseLesson
        fields = ('id', 'chapter', 'name', 'section_type', 'section_link',
                  'duration', 'pub_date', 'free_trail', 'is_show_list', 'course', )


# # 课程章节序列化器
class CourseChapterModelSerializer(ModelSerializer):
    # 一对多，需要指定参数
    coursesections = CourseLessonModelSerializer

    class Meta:
        model = CourseChapter
        fields = ('id', 'chapter', 'name', 'coursesections')




