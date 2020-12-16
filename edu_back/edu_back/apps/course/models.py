from datetime import datetime

from ckeditor_uploader.fields import RichTextUploadingField


from django.db import models

from edu_back.settings.constants import IMG_SRC
from home.models import BaseModel


class CourseCategory(BaseModel):
    """
    课程分类
    """
    name = models.CharField(max_length=64, unique=True, verbose_name="分类名称")

    class Meta:
        db_table = "bz_course_category"
        verbose_name = "课程分类"
        verbose_name_plural = "课程分类"

    def __str__(self):
        return "%s" % self.name


class Course(BaseModel):
    """
    课程信息
    """
    course_type = (
        (0, '收费课程'),
        (1, '高级课程'),
        (2, '专业技能')
    )
    level_choices = (
        (0, '入门'),
        (1, '进阶'),
        (2, '大师'),
    )
    status_choices = (
        (0, '上线'),
        (1, '下线'),
        (2, '预上线'),
    )
    name = models.CharField(max_length=128, verbose_name="课程名称")
    course_img = models.ImageField(upload_to="course", max_length=255, verbose_name="封面图片", blank=True, null=True)
    course_type = models.SmallIntegerField(choices=course_type, default=0, verbose_name="付费类型")
    # 使用这个字段的原因
    brief = RichTextUploadingField(max_length=2048, verbose_name="详情介绍", null=True, blank=True)
    level = models.SmallIntegerField(choices=level_choices, default=1, verbose_name="难度等级")
    pub_date = models.DateField(verbose_name="发布日期", auto_now_add=True)
    period = models.IntegerField(verbose_name="建议学习周期(day)", default=7)
    file_path = models.FileField(max_length=128, verbose_name="课件路径", blank=True, null=True)
    status = models.SmallIntegerField(choices=status_choices, default=0, verbose_name="课程状态")
    course_category = models.ForeignKey("CourseCategory", on_delete=models.CASCADE, null=True, blank=True,
                                        verbose_name="课程分类")
    students = models.IntegerField(verbose_name="学习人数", default=0)
    lessons = models.IntegerField(verbose_name="总课时数量", default=0)
    pub_lessons = models.IntegerField(verbose_name="课时更新数量", default=0)
    price = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="课程原价", default=0)
    teacher = models.ForeignKey("Teacher", on_delete=models.DO_NOTHING, null=True, blank=True, verbose_name="授课老师")

    def active_list(self):
        # 获取当前课程所参与的活动列表
        active_list = self.activeprices.filter(is_show=True, is_delete=False,
                                               active__start_time__lte=datetime.now(),
                                               active__end_time__gte=datetime.now(),
                                               ).order_by("orders")
        return active_list

    @property
    def lesson_list(self):
        """获取当前课程前几节课时用于展示"""
        lesson_list = CourseLesson.objects.filter(is_show=True, is_delete=False, course_id=self.id).all()[:4]
        data_list = []
        for lesson in lesson_list:
            data_list.append({
                "id": lesson.id,
                "name": lesson.name,
                'duration': lesson.duration,
                "free_trail": lesson.free_trail,
                'section_type': lesson.section_type,
                'chapter': lesson.chapter.name,
            })
        return data_list

    @property
    def level_name(self):
        # 自定义课程难度
        return self.level_choices[self.level][1]

    @property
    def course_chapter_list(self):
        # 课程对应的章节列表
        course_chapter_list = CourseChapter.objects.filter(is_delete=False, is_show=True, course_id=self.id).all()
        data_list = []
        if course_chapter_list is []:
            return data_list
        else:
            for course_chapter in course_chapter_list:
                data_list.append({
                    "id": course_chapter.id,
                    "course": course_chapter.course.name,
                    "chapter": course_chapter.chapter,
                    "name": course_chapter.name,
                    "summary": course_chapter.summary,
                    "pub_date": course_chapter.pub_date,
                })
            return data_list

    @property
    def brief_html(self):
        # 返回富文本编辑器中图片的全路径
        # src=/media/2020/12/09/vpfvhb.jpg
        # http://api.baizhiedu.com:8000/media/2020/12/09/vpfvhb.jpg
        brief = self.brief.replace('src="/media', 'src="%s/media' % IMG_SRC)
        return brief

    @property
    def get_file_path(self):
        # 文件路径
        file_path = IMG_SRC + "/media/%s" % self.file_path
        return file_path

    @property
    def active_time(self):
        """计算当前课程所参与活动的倒计时"""
        time = 0
        active_list = self.active_list()

        if len(active_list) > 0:
            active = active_list[0]

            # 获取当前服务器的时间戳
            now_time = datetime.now().timestamp()
            # 获取活动结束的时间戳
            end_time = active.active.end_time.timestamp()
            time = end_time - now_time

            return int(time)
        return int(time)

    @property
    def discount_name(self):
        """如果课程参与了优惠活动，返回当前课程所对应的优惠活动名称"""
        name = "原价"
        active_list = self.active_list()
        if len(active_list) > 0:
            active = active_list[0]
            name = active.discount.discount_type.name

        return name


    @property
    def expire_list(self):
        """获取课程对应的有效期"""
        expires = self.course_expire.filter(is_show=True, is_delete=False)
        data = []
        print(self.price)
        for item in expires:
            price = item.price
            print("有效期对应的价格：", price)
            active_list = self.active_list()
            if len(active_list) > 0:
                """如果课程参与活动才计算活动价格"""
                active = active_list[0]

                # 判断原价是否满足参与优惠的门槛
                condition = active.discount.condition
                sale = active.discount.sale
                self.price = float(price)
                if self.price >= condition:
                    # 判断当前课程满足哪一种优惠条件
                    if sale == "":
                        # 限时免费
                        price = 0
                    elif sale[0] == "*":
                        # 折扣
                        price = self.price * float(sale[1:])
                    elif sale[0] == "-":
                        price = self.price - float(sale[1:])
                    elif sale[0] == "满":
                        """满减 500-40 400-30"""
                        sale_split = sale.split("\r\n")
                        # 处理策略 将满足条件的策略放入列表中
                        price_list = []
                        for sale_item in sale_split:
                            item = sale_item[1:]
                            condition_price, condition_sale = item.split("-")
                            if self.price >= float(condition_price):
                                price_list.append(float(condition_sale))

                        if len(price_list) > 0:
                            # 课程原价减去满足当前条件最大优惠
                            price = self.price - max(price_list)
            else:
                price = item.price

            if item.id != 0:
                data.append({
                    "id": item.id,
                    "expire_text": item.expire_text,
                    "price": price,
                    "all_price": self.price,
                })
            else:
                data.append({
                    "id": item.id,
                    "expire_text": item.expire_text,
                    "price": item.price,
                    "all_price": self,
                })
        if self.price > 0:
            data.append({
                "id": 0,
                "expire_text": "永久有效",
                "price": self.price,
                "all_price": self.price,
            })
        print(data)

        return data

    @property
    def real_price(self):
        """
        计算当前课程参与活动后的活动价格
        原价  课程所参与的活动策略
        """
        price = self.price
        active_list = self.active_list()

        if len(active_list) > 0:
            """如果课程参与活动才计算活动价格"""
            active = active_list[0]

            # 判断原价是否满足参与优惠的门槛
            condition = active.discount.condition
            sale = active.discount.sale
            self.price = float(self.price)
            if self.price >= condition:
                # 判断当前课程满足哪一种优惠条件
                if sale == "":
                    # 限时免费
                    price = 0
                elif sale[0] == "*":
                    # 折扣
                    price = self.price * float(sale[1:])
                elif sale[0] == "-":
                    price = self.price - float(sale[1:])
                elif sale[0] == "满":
                    """满减 500-40 400-30"""
                    sale_split = sale.split("\r\n")
                    # 处理策略 将满足条件的策略放入列表中
                    price_list = []
                    for sale_item in sale_split:
                        item = sale_item[1:]
                        condition_price, condition_sale = item.split("-")
                        if self.price >= float(condition_price):
                            price_list.append(float(condition_sale))

                    if len(price_list) > 0:
                        # 课程原价减去满足当前条件最大优惠
                        price = self.price - max(price_list)

            return price
        return price

    # 计算最终价格(根据有限期计算，要参数有限期的id)
    def final_price(self, expire_id):
        """
        1. 判断当前课时是否永久有效  expire_id > 0
        2. 根据有效期的id拿到有效期对应的价格
        3. 根据有效期价格进行优惠活动处理
        4. 根据不同的规则计算出最终价格
        :return:
        """
        # 如果有效期的id大于0，则需要通过有效期对应的价格来计算活动真实价
        # id不大于0则使用课程本身的原价
        price = self.price
        try:
            if expire_id > 0:
                course_expire = CourseExpire.objects.get(id=expire_id)
                # 对应有效期的价格
                price = course_expire.price
        except CourseExpire.DoesNotExist:
            pass

        active_list = self.active_list()

        if len(active_list) > 0:
            """如果课程参与活动才计算活动价格"""
            active = active_list[0]
            # 判断原价是否满足参与优惠的门槛
            condition = active.discount.condition
            sale = active.discount.sale

            # 判断当前课程满足哪一种优惠条件
            self.price = float(price)
            if self.price >= condition:
                if sale == "":
                    # 限时免费
                    price = 0
                elif sale[0] == "*":
                    # 折扣
                    price = self.price * float(sale[1:])
                elif sale[0] == "-":
                    price = self.price - float(sale[1:])
                elif sale[0] == "满":
                    """满减 500-40 400-30"""
                    sale_split = sale.split("\r\n")
                    # 处理策略 将满足条件的策略放入列表中
                    price_list = []
                    for sale_item in sale_split:
                        item = sale_item[1:]
                        condition_price, condition_sale = item.split("-")
                        if self.price >= float(condition_price):
                            price_list.append(float(condition_sale))

                    if len(price_list) > 0:
                        # 课程原价减去满足当前条件最大优惠
                        price = self.price - max(price_list)

        return price

    class Meta:
        db_table = "bz_course"
        verbose_name = "专题课程"
        verbose_name_plural = "专题课程"

    def __str__(self):
        return "%s" % self.name


class Teacher(BaseModel):
    """讲师表"""
    role_choices = (
        (0, '讲师'),
        (1, '班主任'),
        (2, '教学总监'),
    )
    name = models.CharField(max_length=32, verbose_name="讲师title")
    role = models.SmallIntegerField(choices=role_choices, default=0, verbose_name="讲师身份")
    title = models.CharField(max_length=64, verbose_name="职称")
    signature = models.CharField(max_length=255, verbose_name="导师签名", help_text="导师签名", blank=True, null=True)
    image = models.ImageField(upload_to="teacher", null=True, verbose_name="讲师封面")
    brief = models.TextField(max_length=1024, verbose_name="讲师描述")

    class Meta:
        db_table = "bz_teacher"
        verbose_name = "讲师导师"
        verbose_name_plural = "讲师导师"

    def __str__(self):
        return "%s" % self.name


class CourseChapter(BaseModel):
    """课程章节"""
    course = models.ForeignKey("Course", related_name='coursechapters', on_delete=models.CASCADE, verbose_name="课程名称")
    chapter = models.SmallIntegerField(verbose_name="第几章", default=1)
    name = models.CharField(max_length=128, verbose_name="章节标题")
    summary = models.TextField(verbose_name="章节介绍", blank=True, null=True)
    pub_date = models.DateField(verbose_name="发布日期", auto_now_add=True)

    class Meta:
        db_table = "bz_course_chapter"
        verbose_name = "课程章节"
        verbose_name_plural = "课程章节"

    def __str__(self):
        return "%s:(第%s章)%s" % (self.course, self.chapter, self.name)


class CourseLesson(BaseModel):
    """课程课时"""
    section_type_choices = (
        (0, '文档'),
        (1, '练习'),
        (2, '视频')
    )
    chapter = models.ForeignKey("CourseChapter", related_name='coursesections', on_delete=models.CASCADE,
                                verbose_name="课程章节")
    name = models.CharField(max_length=128, verbose_name="课时标题")
    section_type = models.SmallIntegerField(default=2, choices=section_type_choices, verbose_name="课时种类")
    section_link = models.CharField(max_length=255, blank=True, null=True, verbose_name="课时链接",
                                    help_text="若是video，填vid,若是文档，填link")
    duration = models.CharField(verbose_name="视频时长", blank=True, null=True, max_length=32)  # 仅在前端展示使用
    pub_date = models.DateTimeField(verbose_name="发布时间", auto_now_add=True)
    free_trail = models.BooleanField(verbose_name="是否可试看", default=False)
    course = models.ForeignKey("Course", related_name="course_lesson", on_delete=models.CASCADE, verbose_name="课程")
    is_show_list = models.BooleanField(verbose_name="是否展示到课程", default=False)

    # lesson = models.IntegerField(verbose_name="第几个课时", default="第一个")
    @property
    def chapter_list(self):
        lesson_list = CourseChapter.objects.filter(is_show=True, is_delete=False, id=self.chapter_id).all()[:4]
        data_list = []
        for cpt in lesson_list:
            data_list.append({
                "id": cpt.id,
                "name": cpt.name,
                "chapter": cpt.chapter,
                "summary": cpt.summary,
            })
        return data_list


    class Meta:
        db_table = "bz_course_lesson"
        verbose_name = "课程课时"
        verbose_name_plural = "课程课时"

    def __str__(self):
        return "%s-%s" % (self.chapter, self.name)


class CourseDiscountType(BaseModel):
    """课程优惠类型"""
    name = models.CharField(max_length=32, verbose_name="优惠类型名称")
    remark = models.CharField(max_length=250, blank=True, null=True, verbose_name="备注信息")

    class Meta:
        db_table = "bz_course_discount_type"
        verbose_name = "课程优惠类型"
        verbose_name_plural = "课程优惠类型"

    def __str__(self):
        return "%s" % (self.name)


class CourseDiscount(BaseModel):
    """课程优惠折扣模型"""
    discount_type = models.ForeignKey("CourseDiscountType", on_delete=models.CASCADE, related_name='coursediscounts',
                                      verbose_name="优惠类型")
    condition = models.IntegerField(blank=True, default=0, verbose_name="满足优惠的价格条件",
                                    help_text="设置参与优惠的价格门槛，表示商品必须在xx价格以上的时候才参与优惠活动，<br>如果不填，则不设置门槛")
    sale = models.TextField(verbose_name="优惠公式", blank=True, null=True, help_text="""
    不填表示免费；<br>
    *号开头表示折扣价，例如*0.82表示八二折；<br>
    -号开头则表示减免，例如-20表示原价-20；<br>
    如果需要表示满减,则需要使用 原价-优惠价格,例如表示课程价格大于100,优惠10;大于200,优惠20,格式如下:<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;满100-10<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;满200-25<br>
    """)

    class Meta:
        db_table = "bz_course_discount"
        verbose_name = "价格优惠策略"
        verbose_name_plural = "价格优惠策略"

    def __str__(self):
        return "价格优惠:%s,优惠条件:%s,优惠值:%s" % (self.discount_type.name, self.condition, self.sale)


class Activity(BaseModel):
    """优惠活动"""
    name = models.CharField(max_length=150, verbose_name="活动名称")
    start_time = models.DateTimeField(verbose_name="优惠策略的开始时间")
    end_time = models.DateTimeField(verbose_name="优惠策略的结束时间")
    remark = models.CharField(max_length=250, blank=True, null=True, verbose_name="备注信息")

    class Meta:
        db_table = "bz_activity"
        verbose_name = "商品活动"
        verbose_name_plural = "商品活动"

    def __str__(self):
        return self.name


class CoursePriceDiscount(BaseModel):
    """课程与优惠策略的关系表"""
    course = models.ForeignKey("Course", on_delete=models.CASCADE, related_name="activeprices", verbose_name="课程")
    active = models.ForeignKey("Activity", on_delete=models.DO_NOTHING, related_name="activecourses", verbose_name="活动")
    discount = models.ForeignKey("CourseDiscount", on_delete=models.CASCADE, related_name="discountcourse",
                                 verbose_name="优惠折扣")

    class Meta:
        db_table = "bz_course_price_discount"
        verbose_name = "课程与优惠策略的关系表"
        verbose_name_plural = "课程与优惠策略的关系表"

    def __str__(self):
        return "课程：%s，优惠活动: %s,开始时间:%s,结束时间:%s" % (
            self.course.name, self.active.name, self.active.start_time, self.active.end_time)


class CourseExpire(BaseModel):
    """课程有效期模型"""
    course = models.ForeignKey("Course", related_name='course_expire', on_delete=models.CASCADE,
                               verbose_name="课程名称")
    expire_time = models.IntegerField(verbose_name="有效期", null=True, blank=True, help_text="有效期按天数计算")
    expire_text = models.CharField(max_length=150, verbose_name="提示文本", null=True, blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="课程价格", default=0)

    class Meta:
        db_table = "bz_course_expire"
        verbose_name = "课程有效期"
        verbose_name_plural = verbose_name

    def __str__(self):
        return "课程：%s，有效期：%s，价格：%s" % (self.course, self.expire_text, self.price)
