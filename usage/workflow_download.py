from jmcomic import *
from jmcomic.cl import JmcomicUI

# 下方填入你要下载的本子的id，一行一个，每行的首尾可以有空白字符
jm_albums = ('''
143372
409131
332257
419024
564028
560641
558396
336468
554527
267941
522064
531631
529786
464634
515472
1759
339081
102816
404804
181949
541051
487341
542563
541053
540468
506966
529958
305071
428174
537162
536751
460128
540951
537161
536750
540952
535919
529632
445008
481106
540931
529456
526944
536738
444193
506304
537173
386684
478552
500725
288239
411632
203552
303276
113202
396787
244676
533127
231468
453606
404785
221720
452219
433647
425048
189965
143813
162672
152200
303473
304653
439364
149126
408293
418759
431377
446708
446735
445589
439274
350102
273075
441891
441217
438011
405636
353967
254565
436671
438467
436697
399446
416330
431829
434557
399455
405187
274089
431258
431225
413146
418985
419958
394850
369638
421932
305826
374554
148499
433902
434188
297626
7582
7581
435515
431847
431896
418958
434153
305415
405624
434573
355719
419980
435422
274728
369412
421454
417953
432012
427363
408924
412030
413551
281392
421090
337226
418973
414754
405785
417688
403321
414209
411023
285225
291016
368612
201810
179339
194283
404783
392881
400437
411326
417133
378070
410614
417137
410037
408327
417924
415254
417925
417973
408910
393691
371860
371589
369867
393694
398921
282370
369687
413555
416889
409642
38661
344590
410593
303092
140170
300862
408770
81419
321384
416132
369720
409244
408402
408072
271925
335011
335010
172233
334081
353579
408299
412038
368563
380436
408780
7009
416893
375608
406369
321576
376349
416874
387859
389739
386894
377474
329971
367976
93551
375610
87126
386888
275327
379798
387262
386688
375606
375612
375663
206025
374812
95145
151978
371000
373734
266276
374788
371579
374057
261705
372232
373203
374474
374515
374575
365926
28672
369359
301258
362581
301674
366520
368532
372787
365562
325913
230707
145909
123375
369634
301901
338826
360526
356073
295843
352874
362705
192416
358714
349697
360740
359558
238596
334858
282811
335405
232689
321712
251295
''')

# 单独下载章节
jm_photos = '''



'''


def env(name, default, trim=('[]', '""', "''")):
    import os
    value = os.getenv(name, None)
    if value is None or value == '':
        return default

    for pair in trim:
        if value.startswith(pair[0]) and value.endswith(pair[1]):
            value = value[1:-1]

    return value


def get_id_set(env_name, given):
    aid_set = set()
    for text in [
        given,
        (env(env_name, '')).replace('-', '\n'),
    ]:
        aid_set.update(str_to_set(text))

    return aid_set


def main():
    album_id_set = get_id_set('JM_ALBUM_IDS', jm_albums)
    photo_id_set = get_id_set('JM_PHOTO_IDS', jm_photos)

    helper = JmcomicUI()
    helper.album_id_list = list(album_id_set)
    helper.photo_id_list = list(photo_id_set)

    option = get_option()
    helper.run(option)
    option.call_all_plugin('after_download')


def get_option():
    # 读取 option 配置文件
    option = create_option(os.path.abspath(os.path.join(__file__, '../../assets/option/option_workflow_download.yml')))

    # 支持工作流覆盖配置文件的配置
    cover_option_config(option)

    # 把请求错误的html下载到文件，方便GitHub Actions下载查看日志
    log_before_raise()

    return option


def cover_option_config(option: JmOption):
    dir_rule = env('DIR_RULE', None)
    if dir_rule is not None:
        the_old = option.dir_rule
        the_new = DirRule(dir_rule, base_dir=the_old.base_dir)
        option.dir_rule = the_new

    impl = env('CLIENT_IMPL', None)
    if impl is not None:
        option.client.impl = impl

    suffix = env('IMAGE_SUFFIX', None)
    if suffix is not None:
        option.download.image.suffix = fix_suffix(suffix)


def log_before_raise():
    jm_download_dir = env('JM_DOWNLOAD_DIR', workspace())
    mkdir_if_not_exists(jm_download_dir)

    def decide_filepath(e):
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)

        if resp is None:
            suffix = str(time_stamp())
        else:
            suffix = resp.url

        name = '-'.join(
            fix_windir_name(it)
            for it in [
                e.description,
                current_thread().name,
                suffix
            ]
        )

        path = f'{jm_download_dir}/【出错了】{name}.log'
        return path

    def exception_listener(e: JmcomicException):
        """
        异常监听器，实现了在 GitHub Actions 下，把请求错误的信息下载到文件，方便调试和通知使用者
        """
        # 决定要写入的文件路径
        path = decide_filepath(e)

        # 准备内容
        content = [
            str(type(e)),
            e.msg,
        ]
        for k, v in e.context.items():
            content.append(f'{k}: {v}')

        # resp.text
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)
        if resp:
            content.append(f'响应文本: {resp.text}')

        # 写文件
        write_text(path, '\n'.join(content))

    JmModuleConfig.register_exception_listener(JmcomicException, exception_listener)


if __name__ == '__main__':
    main()
