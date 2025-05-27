"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for Airinnova AB, Stockholm, Sweden

Functions to generate queuing script for Edge:
queue_preprocessor.script and queue_edgesolver.script
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
import subprocess

from ceasiompy import log

# =================================================================================================
#   CLASSES
# =================================================================================================


class EdgeScripts:
    def __init__(self, dir_path, jobname, input_que_script_path, edge_input_file):
        self.jobname = jobname
        self.dir_path = dir_path
        self.input_que_script_path = input_que_script_path
        self.Edge_dir = "/pdc/software/22.06/other/m-edge/3.2/gnu/bin/"
        self.EdgeInputFile = edge_input_file
        # self.GridDir = 'grid'
        # os.chdir(os.path.join(caseDir, self.GridDir))

    def submit_preprocessor_script(self, dir_path):
        preprocessor = os.path.join(self.Edge_dir, "preprocessor")
        # dir_path = self.dir_path
        QueScript = "queue_preprocessor.script"
        Submitcommand = "sbatch"
        os.chdir(dir_path)
        with open(self.input_que_script_path, "r") as template_file, open(
            QueScript, "w"
        ) as que_script:
            for line in template_file:
                if "-J jobname" in line:
                    line = line.replace("-J jobname", f"-J {self.jobname}prepro")
                que_script.write(line)
            que_script.write(f"{preprocessor} {self.EdgeInputFile} > edge_preprocessor.log 2>&1\n")
            print(f"{preprocessor} {self.EdgeInputFile} > edge_preprocessor.log 2>&1\n")
        os.system(f"{Submitcommand} {que_script}")

    def run_preprocessor(self, dir_path):
        # preprocessor = os.path.join(self.Edge_dir, 'preprocessor')
        # dir_path = self.dir_path
        # QueScript = f'queue_preprocessor.script'
        # Submitcommand = 'sbatch'
        os.chdir(dir_path)

        """
        with open(self.input_que_script_path, 'r') as template_file,
        open(QueScript, 'w') as que_script:
            for line in template_file:
                if '-J jobname' in line:
                    line = line.replace('-J jobname', f'-J {self.jobname}prepro')
                que_script.write(line)
            que_script.write(f'{preprocessor} {self.EdgeInputFile} > edge_preprocessor.log 2>&1\n')
            print(f'{preprocessor} {self.EdgeInputFile} > edge_preprocessor.log 2>&1\n')
        """
        os.system(f"preprocessor {self.EdgeInputFile} > edge_preprocessor.log 2>&1\n")

    def submit_solver_script(self, dir_path, nb_proc):
        run_solver = os.path.join(self.Edge_dir, "edge_mpi_run")
        QueScript = "queue_edgesolver.script"
        # dir_path = self.dir_path
        Submitcommand = "sbatch"
        os.chdir(dir_path)
        with open(self.input_que_script_path, "r") as template_file, open(
            QueScript, "w"
        ) as que_script:
            for line in template_file:
                if "-J jobname" in line:
                    line = line.replace("-J jobname", f"-J {self.jobname}solver")
                que_script.write(line)
            que_script.write(f"{run_solver} {self.EdgeInputFile} {nb_proc} > edge_run.log 2>&1\n")
        os.system(f"{Submitcommand} {que_script}")

    def run_edgesolver(self, dir_path, nb_proc):
        run_solver = os.path.join(self.Edge_dir, "edge_mpi_run")
        os.chdir(dir_path)
        os.system(f"{run_solver} {self.EdgeInputFile} {nb_proc} > edge_run.log 2>&1\n")

    def postprocess_script(self, dir_path, edge_grid):
        # ffaucut = os.path.join(self.Edge_dir, 'ffaucut')
        # ffauinterpol = os.path.join(self.Edge_dir, 'ffauinterpol')
        # ffa2tab = os.path.join(self.Edge_dir, 'ffa2tab')
        ffa2engold = os.path.join(self.Edge_dir, "ffa2engold")
        grid = edge_grid

        # output file names
        # walldata1 = "Edge_wall.dat"
        # walldata2 = "Edge_wall.cf"
        # forcemoments = "Edge_force_moment.dat"
        ensgoldprefix = "zzz"
        solution1 = "Edge.bout"
        # solution2 = "Post.bout"

        # Enter the folder
        os.chdir(dir_path)

        """
        # Extract the boundary
        input_data =
        1
        0
        with subprocess.Popen([ffaucut, grid, 'tmp1'], stdin=subprocess.PIPE, text=True)
         as process:
            process.communicate(input=input_data)


        # Inteerpolate the soulutions
        subprocess.run([ffauinterpol, solution1, 'tmp1', 'tmp11'])
        subprocess.run([ffauinterpol, solution2, 'tmp1', 'tmp12'])

        # Extract tabulated data
        subprocess.run([ffa2tab, 'tmp11', walldata1])
        subprocess.run([ffa2tab, 'tmp12', walldata2])

        # Cleanup
        for temp_file in ['tmp1', 'tmp11', 'tmp12']:
            os.remove(temp_file)
        """
        # Create ensight gold files
        subprocess.run([ffa2engold, grid, solution1, ensgoldprefix])

        # os.system(f'{Submitcommand} {que_script}')


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
