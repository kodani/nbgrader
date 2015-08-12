import os
import glob
import shutil
import re

from IPython.utils.traitlets import Bool

from nbgrader.apps.baseapp import TransferApp, transfer_aliases, transfer_flags


aliases = {}
aliases.update(transfer_aliases)
aliases.update({
})

flags = {}
flags.update(transfer_flags)
flags.update({
    'inbound': (
        {'ListApp' : {'inbound': True}},
        "List inbound files rather than outbound."
    ),
    'remove': (
        {'ListApp' : {'remove': True}},
        "Remove an assignment from the exchange."
    ),
})

class ListApp(TransferApp):

    name = u'nbgrader-list'
    description = u'List assignments in the nbgrader exchange'

    aliases = aliases
    flags = flags

    examples = """
        List assignments in the nbgrader exchange. For the usage of instructors
        and students.

        Students
        ========

        To list assignments for a course, you must first know the `course_id` for
        your course. If you don't know it, ask your instructor.

        To list the released assignments for the course `phys101`:

            nbgrader list phys101

        Instructors
        ===========

        To list outbound (released) or inbound (submitted) assignments for a course,
        you must configure the `course_id` in your config file or the command line.

        To see all of the released assignments, run

            nbgrader list  # course_id in the config file

        or

            nbgrader list --course phys101  # course_id provided

        To see the inbound (submitted) assignments:

            nbgrader list --inbound

        You can use the `--student` and `--assignment` options to filter the list
        by student or assignment:

            nbgrader list --inbound --student=student1 --assignment=assignment1

        If a student has submitted an assignment multiple times, the `list` command
        will show all submissions with their timestamps.

        The `list` command can optionally remove listed assignments by providing the
        `--remove` flag:

            nbgrader list --inbound --remove --student=student1
        """

    inbound = Bool(False, config=True, help="List inbound files rather than outbound.")
    remove = Bool(False, config=True, help="Remove, rather than list files.")

    def init_src(self):
        pass

    def init_dest(self):
        course_id = self.course_id if self.course_id else '*'
        assignment_id = self.assignment_id if self.assignment_id else '*'
        student_id = self.student_id if self.student_id else '*'

        if self.inbound:
            pattern = os.path.join(self.exchange_directory, course_id, 'inbound', '{}+{}+*'.format(student_id, assignment_id))
        else:
            pattern = os.path.join(self.exchange_directory, course_id, 'outbound', '{}'.format(assignment_id))

        self.assignments = sorted(glob.glob(pattern))

    def parse_inbound_assignment(self, assignment):
        regexp = r".*/(?P<course_id>.*)/inbound/(?P<student_id>.*)\+(?P<assignment_id>.*)\+(?P<timestamp>.*)"
        m = re.match(regexp, assignment)
        if m is None:
            raise RuntimeError("Could not match '%s' with regexp '%s'", assignment, regexp)
        return m.groupdict()

    def parse_outbound_assignment(self, assignment):
        regexp = r".*/(?P<course_id>.*)/outbound/(?P<assignment_id>.*)"
        m = re.match(regexp, assignment)
        if m is None:
            raise RuntimeError("Could not match '%s' with regexp '%s'", assignment, regexp)
        return m.groupdict()

    def format_inbound_assignment(self, assignment):
        info = self.parse_inbound_assignment(assignment)
        return "{course_id} {student_id} {assignment_id} {timestamp}".format(**info)

    def format_outbound_assignment(self, assignment):
        info = self.parse_outbound_assignment(assignment)
        return "{course_id} {assignment_id}".format(**info)

    def copy_files(self):
        pass

    def list_files(self):
        """List files."""
        if self.inbound:
            self.log.info("Submitted assignments:")
            for path in self.assignments:
                self.log.info(self.format_inbound_assignment(path))

        else:
            self.log.info("Released assignments:")
            for path in self.assignments:
                self.log.info(self.format_outbound_assignment(path))

    def remove_files(self):
        """List and remove files."""
        if self.inbound:
            self.log.info("Removing submitted assignments:")
            for path in self.assignments:
                self.log.info(self.format_inbound_assignment(path))
                shutil.rmtree(path)
        else:
            self.log.info("Removing released assignments:")
            for path in self.assignments:
                self.log.info(self.format_outbound_assignment(path))
                shutil.rmtree(path)

    def start(self):
        if len(self.extra_args) == 0:
            self.extra_args = ["*"] # allow user to not put in assignment
        super(ListApp, self).start()
        if self.remove:
            self.remove_files()
        else:
            self.list_files()
