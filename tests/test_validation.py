import formencode, tw.core as twc, testapi


compound_widget = twc.CompoundWidget(id='a', children=[
    twc.Widget(id='b', validator=twc.Validator(required=True)),
    twc.Widget(id='c', validator=twc.Validator(required=True)),
])

repeating_widget = twc.RepeatingWidget(id='a', child=
    twc.Widget(id='b', validator=twc.Validator(required=True))
)

class TestValidation(object):
    def setUp(self):
        testapi.setup()

    def test_call_validator(self):
        try:
            twc.validation.call_validator(formencode.validators.Int, 'x')
            assert(False)
        except twc.ValidationError:
            pass

    def test_unflatten(self):
        assert(twc.validation.unflatten_params({'a':1, 'b:c':2}) ==
            {'a':1, 'b':{'c':2}})
        assert(twc.validation.unflatten_params({'a:b:c':2}) ==
            {'a': {'b':{'c':2}}})
        assert(twc.validation.unflatten_params({'a:b:c':2, 'a:b:d':3}) ==
            {'a': {'b':{'c':2, 'd':3}}})
        assert(twc.validation.unflatten_params({'a:b:c':2, 'a:b:d':3, 'a:e':4}) ==
            {'a': {'b':{'c':2, 'd':3}, 'e':4}})

        assert(twc.validation.unflatten_params({'a:1':20, 'a:2':10}) ==
            {'a':[20, 10]})
        assert(twc.validation.unflatten_params({'a:1':20, 'b:2':10}) ==
            {'a':[20], 'b':[10]})
        assert(twc.validation.unflatten_params({'a:1':20, 'a:x':10}) ==
            {'a':{'1':20, 'x':10}})

    def test_decode(self):
        ustr = u'abc\u1234'
        assert(twc.Validator().to_python(ustr.encode('utf-8')) == ustr)

    def test_decode_error(self):
        try:
            twc.Validator().to_python('abc\xC3')
            assert(False)
        except twc.ValidationError, e:
            print e
            assert(str(e) == 'Received in the wrong character set')

    def test_strip(self):
        assert(twc.Validator().to_python(' a ') == 'a')
        assert(twc.Validator(strip=False).to_python(' a ') == ' a ')

    def test_auto_unflatten(self):
        test = twc.CompoundWidget(id='a', children=[
            twc.Widget(id='b', validator=twc.Validator(required=True)),
        ])
        testapi.request(1)
        assert(test.validate({'a:b':'10'}) == {'b':'10'})

    def test_meta_msgs(self):
        class A(object):
            __metaclass__ = twc.validation.ValidatorMeta
            msgs = {'a':'b'}
        class B(A):
            msgs = {'b':'c'}
        assert(B.msgs == {'a':'b', 'b':'c'})

    def test_meta_super(self):
        class MyVld(twc.Validator):
            def validate_python(self, value):
                pass
        try:
            MyVld(required=True).to_python(None)
            assert(False)
        except twc.ValidationError:
            pass

    def test_process_validate(self):
        class MyValidator(twc.Validator):
            def from_python(self, value):
                return value.upper()
        test = twc.Widget(id='a', template='b', validator=MyValidator())
        testapi.request(1)
        test.value = 'fred'
        test.process()
        assert(test.value == 'FRED')

    def test_ve_string(self):
        try:
            raise twc.ValidationError('this is a test')
        except twc.ValidationError, e:
            assert(str(e) == 'this is a test')

    def test_ve_rewrite(self):
        try:
            raise twc.ValidationError('required')
        except twc.ValidationError, e:
            assert(str(e) == 'Please enter a value')

    def test_ve_subst(self):
        try:
            vld = twc.IntValidator(max=10)
            raise twc.ValidationError('toobig', vld)
        except twc.ValidationError, e:
            assert(str(e) == 'Cannot be more than 10')

    def test_vld_leaf_pass(self):
        test = twc.Widget(validator=twc.IntValidator())
        testapi.request(1)
        assert(test.validate('1') == 1)

    def test_vld_leaf_fail(self):
        test = twc.Widget(validator=twc.IntValidator())
        testapi.request(1)
        try:
            test.validate('x')
            assert(False)
        except twc.ValidationError:
            pass

        assert(test.orig_value == 'x')
        assert(test.error_msg == 'Must be an integer')

    def test_compound_pass(self):
        testapi.request(1)
        inp = {'a': {'b':'test', 'c':'test2'}}
        out = compound_widget.validate(inp)
        assert(out == inp['a'])
        assert(compound_widget.children.b.orig_value == 'test')
        assert(compound_widget.children.c.orig_value == 'test2')

    def test_compound_corrupt(self):
        testapi.request(1)
        try:
            compound_widget.validate({'a':[]})
            assert(False)
        except twc.ValidationError:
            pass

    def test_compound_child_fail(self):
        testapi.request(1)
        try:
            compound_widget.validate({'a': {'b':'test'}})
            assert(False)
        except twc.ValidationError:
            pass
        assert(compound_widget.children.b.orig_value == 'test')
        assert('enter a value' in compound_widget.children.c.error_msg)

    def test_compound_whole_validator(self):
        pass # TBD

    def test_rw_pass(self):
        testapi.request(1)
        inp = ['test', 'test2']
        out = repeating_widget.validate(inp)
        assert(inp == out)
        assert(repeating_widget.children[0].orig_value == 'test')
        assert(repeating_widget.children[1].orig_value == 'test2')

    def test_rw_corrupt(self):
        testapi.request(1)
        try:
            repeating_widget.validate({'a':[]})
            assert(False)
        except twc.ValidationError:
            pass

    def test_rw_child_fail(self):
        testapi.request(1)
        try:
            repeating_widget.validate(['test', ''])
            assert(False)
        except twc.ValidationError, e:
            pass
        assert(repeating_widget.children[0].orig_value == 'test')
        assert('enter a value' in repeating_widget.children[1].error_msg)

    def test_dow(self):
        test = twc.DisplayOnlyWidget(child=compound_widget)
        testapi.request(1)
        inp = {'a': {'b':'test', 'c':'test2'}}
        out = test.validate(inp)
        assert(out == inp['a'])
        assert(test.child.c.b.orig_value == 'test')
        assert(test.child.c.c.orig_value == 'test2')

    #--
    # Test round trip
    #--
    def test_round_trip(self):
        test = twc.CompoundWidget(id='a', children=[
            twc.DisplayOnlyWidget(id='q', child= # TBD
                twc.RepeatingWidget(id=None, child=
                    twc.Widget(id='b')
                )
            ),
            twc.CompoundWidget(id='cc', children=[
                twc.Widget(id='d'),
                twc.Widget(id='e'),
            ])
        ])

        widgets = [
            test.c[0].child.children[0],
            test.c[0].child.children[1],
            test.c.cc.c.d,
            test.c.cc.c.e,
        ]

        data = dict((w._compound_id, 'test%d' % i) for i,w in enumerate(widgets))
        testapi.request(1)
        vdata = test.validate(data)
        for i,w in enumerate(widgets):
            assert(w.orig_value == 'test%d' % i)
