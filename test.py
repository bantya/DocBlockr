import sublime
import sublime_plugin
import unittest

class DocBlockrTestReplaceCursorPosition(sublime_plugin.TextCommand):
    def run(self, edit):
        cursor_placeholder = self.view.find('\|', 0)
        if cursor_placeholder.empty():
            return

        self.view.sel().clear()
        self.view.sel().add(cursor_placeholder.begin())
        self.view.replace(edit, cursor_placeholder, '')

class ViewTestCase(unittest.TestCase):

    def setUp(self):
        self.window = sublime.active_window()
        self.view = self.window.new_file()
        self.view.set_scratch(True)

        if int(sublime.version()) < 3000:
            self.edit = self.view.begin_edit()

    def tearDown(self):
        if int(sublime.version()) < 3000:
            self.view.sel().clear()
            self.view.end_edit(self.edit)
            self.window.run_command('close')
        else:
            self.view.close()

    def set_view_content(self, content):
        self.view.run_command('insert', {'characters': content})
        self.view.run_command('doc_blockr_test_replace_cursor_position')

        # Allows overriding with custom syntax
        php_syntax_file = self.view.settings().get('doc_blockr_tests_php_syntax_file')
        if not php_syntax_file:
            self.view.set_syntax_file('Packages/PHP/PHP.tmLanguage')
        else:
            self.view.set_syntax_file(php_syntax_file)

    def get_view_content(self):
        return self.view.substr(sublime.Region(0, self.view.size()))

    def run_doc_blockr(self):
        self.view.run_command('jsdocs')

    def assertDocBlockrResult(self, expected):
        if isinstance(expected, list):
            expected = '\n'.join(expected)

        # TODO test selections; for now just removing the placeholders
        expected = expected.replace('|SELECTION_BEGIN|', '')
        expected = expected.replace('|SELECTION_END|', '')

        self.assertEquals(expected, self.get_view_content())

class TestPHP(ViewTestCase):

    def test_basic(self):
        self.set_view_content("/**|\nbasic")
        self.run_doc_blockr()
        self.assertDocBlockrResult('/**\n * \n */\nbasic')

    def test_issue_292_php_args_pass_by_reference_missing_ampersand_char(self):
        self.set_view_content("/**|\nfunction function_name($a1,  $a2 = 'x', array $a3, &$b1, &$b2 = 'x', array &$b3) {}")
        self.run_doc_blockr()
        self.assertDocBlockrResult([
            "/**",
            " * |SELECTION_BEGIN|[function_name description]|SELECTION_END|",
            " * @param  [type] $a1  [description]",
            " * @param  string $a2  [description]",
            " * @param  array  $a3  [description]",
            " * @param  [type] &$b1 [description]",
            " * @param  string &$b2 [description]",
            " * @param  array  &$b3 [description]",
            " * @return [type]      [description]",
            " */",
            "function function_name($a1,  $a2 = 'x', array $a3, &$b1, &$b2 = 'x', array &$b3) {}"
        ])

    def test_issue_286_php_args_namespace_char_is_missing(self):
        self.set_view_content("/**|\nfunction function_name(A\\NS\\ClassName $class) {}")
        self.run_doc_blockr()
        self.assertDocBlockrResult([
            "/**",
            " * |SELECTION_BEGIN|[function_name description]|SELECTION_END|",
            " * @param  A\\NS\\ClassName $class [description]",
            " * @return [type]                [description]",
            " */",
            "function function_name(A\\NS\\ClassName $class) {}"
        ])

    def test_issue_312_array_type_missing_when_param_is_null(self):
        self.set_view_content("/**|\nfunction fname(array $a, array $b = null) {}")
        self.run_doc_blockr()
        self.assertDocBlockrResult([
            "/**",
            " * |SELECTION_BEGIN|[fname description]|SELECTION_END|",
            " * @param  array      $a [description]",
            " * @param  array|null $b [description]",
            " * @return [type]        [description]",
            " */",
            "function fname(array $a, array $b = null) {}"
        ])

    def test_issue_312_qualified_namespace_type_missing_when_param_is_null(self):
        self.set_view_content("/**|\nfunction fname(NS\\ClassA $a, NS\\ClassB $b = null) {}")
        self.run_doc_blockr()
        self.assertDocBlockrResult([
            "/**",
            " * |SELECTION_BEGIN|[fname description]|SELECTION_END|",
            " * @param  NS\\ClassA      $a [description]",
            " * @param  NS\\ClassB|null $b [description]",
            " * @return [type]            [description]",
            " */",
            "function fname(NS\\ClassA $a, NS\\ClassB $b = null) {}"
        ])

    def test_issue_312_fully_qualified_namespace_type_missing_when_param_is_null(self):
        self.set_view_content("/**|\nfunction fname(\\NS\\ClassA $a, \\NS\\ClassB $b = null) {}")
        self.run_doc_blockr()
        self.assertDocBlockrResult([
            "/**",
            " * |SELECTION_BEGIN|[fname description]|SELECTION_END|",
            " * @param  \\NS\\ClassA      $a [description]",
            " * @param  \\NS\\ClassB|null $b [description]",
            " * @return [type]             [description]",
            " */",
            "function fname(\\NS\\ClassA $a, \\NS\\ClassB $b = null) {}"
        ])

    def test_issue_371_with_long_array_syntax(self):
        self.set_view_content("/**|\npublic function test(array $foo = array()) {}")
        self.run_doc_blockr()
        self.assertDocBlockrResult([
            "/**",
            " * |SELECTION_BEGIN|[test description]|SELECTION_END|",
            " * @param  array  $foo [description]",
            " * @return [type]      [description]",
            " */",
            "public function test(array $foo = array()) {}"
        ])

    def test_issue_371_method_with_short_array_syntax(self):
        self.set_view_content("/**|\npublic function test(array $foo = []) {}")
        self.run_doc_blockr()
        self.assertDocBlockrResult([
            "/**",
            " * |SELECTION_BEGIN|[test description]|SELECTION_END|",
            " * @param  array  $foo [description]",
            " * @return [type]      [description]",
            " */",
            "public function test(array $foo = []) {}"
        ])

    def test_issue_371_method_with_short_array_syntax_with_whitespace(self):

        self.set_view_content("/**|\npublic function test(  array   $foo    =     [      ]       ) {}")
        self.run_doc_blockr()
        self.assertDocBlockrResult([
            "/**",
            " * |SELECTION_BEGIN|[test description]|SELECTION_END|",
            " * @param  array  $foo [description]",
            " * @return [type]      [description]",
            " */",
            "public function test(  array   $foo    =     [      ]       ) {}"
        ])

    def test_issue_372_property_with_short_array_syntax(self):
        self.set_view_content("/**|\nprotected $test = [];")
        self.run_doc_blockr()
        self.assertDocBlockrResult([
            "/**",
            " * |SELECTION_BEGIN|[$test description]|SELECTION_END|",
            " * @var array",
            " */",
            "protected $test = [];"
        ])

class RunDocBlockrTests(sublime_plugin.WindowCommand):

    def run(self):
        print('---------------')
        print('DocBlockr Tests')
        print('---------------')

        self.window.run_command('show_panel', {'panel': 'console'})

        unittest.TextTestRunner(verbosity=1).run(
            unittest.TestLoader().loadTestsFromTestCase(TestPHP)
        )

        self.window.focus_group(self.window.active_group())