import random
import pandas as pd
import gurobipy as gp
from gurobipy import GRB
################################################################################################
################################################################################################

# number of students
I = int(input("How many students are in the class?\n"))

# number of projects
J = int(input("How many project options are there?\n"))
projects = [f"Project {(j+1):02d}" for j in range(J)]

# enter student names
roster = []
for i in range(I):
    roster.append(input("Enter Student " + str(i+1 ) + "'s name: "))

#print(students)
print(roster)

# students rank each project
rank_df = pd.DataFrame([
        [7, 1, 2, 6, 4, 3, 5],
        [4, 3, 5, 6, 2, 1, 7],
        [2, 3, 7, 6, 4, 5, 1],
        [2, 1, 3, 6, 7, 5, 4],
        [1, 3, 4, 2, 5, 6, 7],
        [2, 6, 5, 4, 3, 1, 7],
        [2, 1, 7, 3, 4, 6, 5],
        [1, 3, 4, 2, 7, 5, 6],
        [4, 2, 3, 5, 6, 1, 7],
        [2, 3, 1, 7, 4, 5, 6],
        [6, 7, 3, 5, 4, 2, 1],
        [3, 5, 6, 4, 7, 2, 1],
        [1, 3, 7, 2, 6, 4, 5],
        [4, 6, 7, 5, 1, 3, 2],
        [5, 1, 7, 2, 6, 3, 4],
        [3, 2, 6, 4, 5, 1, 7],
        [4, 6, 7, 5, 3, 2, 1],
        [4, 6, 7, 5, 3, 2, 1],
        [1, 3, 5, 4, 6, 7, 2]
    ],
    index=roster,
    columns=projects,
)
rank_df

################################################################################################
################################################################################################

together = [
    ("Skyler", "Josiah"),
    ("Pauline","Amiyah"),
    ("Layra", "Jaslin"),
    ("Dorien", "Jacob"),
    ("Effie", "Hellen"),
    ("Zion", "Jorvi"),
    ("Ramata", "Anaiah"),
    ("Ramata", "Saniyah"),
    ("Saniyah", "Anaiah")
]

apart = [
    ("Zion", "Jacob")
]
################################################################################################
################################################################################################

permutations, ratings = gp.multidict({
    (i, j): rank_df.loc[i, j]
    for i in roster
    for j in projects
})




MAX_STUDENTS_PER_PROJECT = int(input("What is the maximum number of students in a group?\n"))
MIN_STUDENTS_PER_PROJECT = int(input("What is the minimum number of students in a group?\n"))


################################################################################################
################################################################################################

def solve(max_projects):
    # initialize the model object
    m = gp.Model(f"project_assignment_{max_projects}")

    assign = m.addVars(permutations, vtype=GRB.BINARY, name="assign")
    use_project = m.addVars(projects, vtype=GRB.BINARY, name="use_project")

    # each student has one and only one project group
    m.addConstrs(
        (assign.sum(student, "*") == 1 for student in roster),
        name="EachStudentAssignedToOneProject"
    )

    # projects can't exceed the maximum number of students
    m.addConstrs(
        (assign.sum("*", project) <= MAX_STUDENTS_PER_PROJECT for project in projects),
        name="LimitGroupSize"
    )

    # projects must be considered 'in use' if any students are assigned
    m.addConstrs(
        (use_project[project] >= assign[(student, project)] for student in roster for project in projects),
        name="ProjectMustBeInUseIfAnyStudentsAssigned"
    )

    # don't exceed max number of projects
    m.addConstr(use_project.sum() <= max_projects, name="MaxProjects")

    # if any students are assigned to a project, the project must have at least 2 students
    m.addConstrs(
        (assign.sum("*", project) >= use_project[project] * MIN_STUDENTS_PER_PROJECT for project in projects),
        name="ProjectsInUseMustHaveAtLeastTwoStudents"
    )

    # put students together who both indicated the other
    for student1, student2 in together:
        m.addConstrs(
            (assign[(student1, project)] == assign[(student2, project)] for project in projects),
            name=f"PairStudents[{(student1, student1)}]"
        )
    
    # keep students apart who contraindicated another

    for student1, student2 in apart:
        m.addConstrs(
            (
                (assign[(student1, project)] + assign[(student2, project)]
            ) <= 1 for project in projects),
            name=f"ApartStudents[{(student1, student1)}]"
        )

    # set the objective function to be minimized
    m.setObjective(
        (ratings.prod(assign) - 1) ** 2,
        sense=GRB.MINIMIZE,
    )

    m.optimize()
    return m, assign




################################################################################################
################################################################################################
def get_results(assign):
    """ Take the dict of results and turn it into useful DataFrames """
    
    # create df with impossible placeholder
    assign_df = pd.DataFrame(-1, index=roster, columns=projects)

    # fill in the decision variable results
    for (i, j), x_ij in assign.items():
        assign_df.loc[i, j] = int(x_ij.X)

    # sanity check that none were missed
    assert ((assign_df == 0) | (assign_df == 1)).all().all()
    
    # count how many students got their nth choice
    choices = (assign_df * rank_df).values.ravel()
    choices = choices[choices > 0]
    n_ranks = pd.Series(choices).value_counts().rename(index=lambda x: f"choice {x}")

    # count up how big the group sizes are
    group_sizes = assign_df.sum(axis="rows").sort_values(ascending=False).rename("n").sort_values(ascending=False)
    
    return assign_df, n_ranks, group_sizes

################################################################################################
################################################################################################

m, assign = solve(max_projects=5)
assign_df, n_ranks, group_sizes = get_results(assign)

print(n_ranks)
print(group_sizes)
print(assign_df)


