import tw.core as twc, testapi

class Test6(twc.Widget):
    test = twc.Param(attribute=True)

class TestWidgets(object):
    def setUp(self):
        testapi.setup()

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
        test = Test6(id='test', template='test', test='wibble').req()
        test.prepare()
        assert(test.attrs['test'] == 'wibble')

    # this behaviour is removed
    def xxtest_attribute_clash(self):
        test = Test6(id='test', template='test', test='wibble')
        test.attrs = {'test':'blah'}
        try:
            test.process()
            assert(False)
        except twc.ParameterError:
            pass

    def test_deferred(self):
        test = twc.Widget(id='test', template=twc.Deferred(lambda: 'test'))
        assert(test.template != 'test')
        ins = test.req()
        ins.prepare()
        assert(ins.template == 'test')

    def test_child_attr(self):
        class LayoutContainer(twc.CompoundWidget):
            label = twc.ChildParam(default='b')
        test = LayoutContainer(children=[twc.Widget(id='a', label='a')]).req()
        assert(test.c.a.label == 'a')
        test = LayoutContainer(children=[twc.Widget(id='a')]).req()
        assert(test.c.a.label == 'b')

