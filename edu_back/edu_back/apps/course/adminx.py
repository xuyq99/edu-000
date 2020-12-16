import xadmin

from course import models
from course.models import CourseCategory, Course, Teacher, CourseChapter, CourseLesson


class CourseCategoryAdmin(object):
    """课程分类表"""
    pass


xadmin.site.register(CourseCategory, CourseCategoryAdmin)


class CourseAdmin(object):
    """课程信息表"""
    pass


xadmin.site.register(Course, CourseAdmin)


class TeacherAdmin(object):
    """讲师表"""
    pass


xadmin.site.register(Teacher, TeacherAdmin)


class CourseChapterAdmin(object):
    """章节表"""
    pass


xadmin.site.register(CourseChapter, CourseChapterAdmin)


class CourseLessonAdmin(object):
    """课时表"""
    pass


xadmin.site.register(CourseLesson, CourseLessonAdmin)


class CourseDiscountAdmin(object):
    """课程折扣模型"""
    pass


xadmin.site.register(models.CourseDiscount)


class CourseDiscountTypeAdmin(object):
    """课程优惠类型模型"""
    pass


xadmin.site.register(models.CourseDiscountType, CourseDiscountTypeAdmin)


class ActivityAdmin(object):
    """课程优惠时间表"""
    pass


xadmin.site.register(models.Activity, ActivityAdmin)


class CoursePriceDiscountAdmin(object):
    pass


xadmin.site.register(models.CoursePriceDiscount, CoursePriceDiscountAdmin)


class CourseExpireAdmin(object):
    pass


xadmin.site.register(models.CourseExpire, CourseExpireAdmin)