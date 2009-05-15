import tw.core as twc, testapi

class Test(object):
    __metaclass__ = twc.widgets.WidgetMeta
    test1 = twc.Param('test_1', default=10)

class Test2(Test):
    test2 = twc.Param('test_2', default=20)

class TestContainer(twc.CompoundWidget):
    test = twc.ChildParam(default=10)
    test2 = twc.ChildParam()

class Test6(twc.Widget):
    test = twc.Param(attribute=True)

class Test7(twc.Widget):
    test = twc.Param()


class TestWidgets(object):
    def setUp(self):
        testapi.setup()

    #---
    # WidgetMeta
    #--
    def test_parameter(self):
        "Check a simple parameter"

        class Test(object):
            __metaclass__ = twc.widgets.WidgetMeta
            test1 = twc.Param('test_1', default=10)

        assert(len(Test._params) == 1)
        assert(Test._params['test1'].description == 'test_1')
        assert(Test.test1 == 10)

    def test_inherit(self):
        "Check inheritence"
        assert(len(Test2._params) == 2)
        assert(Test2._params['test1'].description == 'test_1')
        assert(Test2._params['test2'].description == 'test_2')
        assert(Test2.test1 == 10)
        assert(Test2.test2 == 20)

    def test_multi_inherit(self):
        "Check multiple inheritence"
        class Test3(Test):
            test3 = twc.Param('test_3')
        class Test4(Test2, Test3):
            pass
        assert(len(Test4._params) == 3)
        assert(sorted(Test4._params.keys()) == ['test1', 'test2', 'test3'])

    def test_override(self):
        "Check overriding a parameter"
        class Test8(Test):
            test1 = twc.Param(request_local=False)
        assert(Test8._params['test1'].default == 10)
        assert(Test._params['test1'].request_local == True)
        assert(Test8._params['test1'].request_local == False)

    def test_override_default(self):
        "Check overriding a parameter default"
        class Test5(Test):
            test1 = 11
        assert(Test5._params['test1'].default == 11)
        assert(Test._params['test1'].default == 10)
        assert(Test5.test1 == 11)

    def test_child(self):
        assert(not hasattr(TestContainer, 'test'))
        test = twc.Widget.cls(id='q')
        assert(not hasattr(test, 'test'))
        test2 = TestContainer.cls(id='r', children=[test]).req()
        assert(test2.c.q.test == 10)

    def xxtest_locked(self):
        class Test(twc.Widget):
            def __init__(self, **kw):
                super(Test, self).__init__(**kw)
                assert(self._locked == False)
        test = Test()
        assert(test._locked == True)

    def xxtest_locked_attrs(self):
        test = twc.Widget()
        object.__setattr__(test, '_locked', False)
        test.id = 'blah'
        test._locked = True
        try:
            test.id = 'lah'
            assert(False)
        except twc.ParameterError:
            pass

    #--
    # Widget.process
    #--
    def xxtest_required(self):
        test = twc.Widget(id='test')
        try:
            test.req()
            assert(False)
        except twc.ParameterError, e:
            assert(str(e) == 'Widget is missing required parameter template')

    def test_attribute(self):
        test = Test6.cls(id='test', template='test', test='wibble').req()
        assert(test.attrs['test'] == 'wibble')

    # this behaviour is removed
    def xxtest_attribute_clash(self):
        test = Test6.cls(id='test', template='test', test='wibble')
        test.attrs = {'test':'blah'}
        try:
            test.process()
            assert(False)
        except twc.ParameterError:
            pass

    def test_deferred(self):
        test = twc.Widget.cls(id='test', template=twc.Deferred(lambda: 'test'))
        assert(test.template != 'test')
        assert(test.req().template == 'test')

    def test_child_attr(self):
        class LayoutContainer(twc.CompoundWidget):
            label = twc.ChildParam(default='b')
        test = LayoutContainer.cls(children=[twc.Widget.cls(id='a', label='a')]).req()
        assert(test.c.a.label == 'a')
        test = LayoutContainer.cls(children=[twc.Widget.cls(id='a')]).req()
        assert(test.c.a.label == 'b')

